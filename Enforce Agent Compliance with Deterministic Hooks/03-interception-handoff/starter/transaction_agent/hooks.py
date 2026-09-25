"""Compliance hooks registered on the :class:`HookEngine`.

Each hook is a deterministic check — the enforcement is programmatic, not prompt-based, so a
zero-tolerance rule (KYC before money movement, no over-threshold transfers) cannot leak.

The KYC prerequisite gate and the PostToolUse normalization hook are complete from steps 1
and 2. In this step you implement the interception path: ``score_risk_flags``,
``build_handoff_summary``, and the ``amount_threshold_hook`` that redirects over-threshold
transfers to compliance review.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from transaction_agent.config import TRANSFER_THRESHOLD
from transaction_agent.models import HandoffSummary, HookDecision, SessionState, ToolCall
from transaction_agent.money import (
    coerce_money,
    normalize_currency,
    normalize_status,
    normalize_timestamp,
)
from transaction_agent.tools import load_customer

CustomerLoader = Callable[[str], dict[str, Any]]

#: Tools that move money and therefore require a completed KYC prerequisite.
MONEY_MOVEMENT_TOOLS = frozenset({"initiate_transfer", "adjust_balance", "resolve_dispute"})

#: Key families the PostToolUse normalization hook recognizes.
_MONETARY_KEYS = frozenset({"amount", "balance"})
_TIMESTAMP_KEYS = frozenset({"timestamp", "date"})
_STATUS_KEYS = frozenset({"status", "status_code"})


def kyc_prerequisite_hook(call: ToolCall, state: SessionState) -> HookDecision:
    """Block money-movement tools until ``verify_kyc`` has recorded a verified id for the customer.

    The canonical prerequisite is "a tool returned a verified customer ID"; the engine records
    that id on a successful ``verify_kyc`` and this hook gates on its presence.
    """
    if call.name in MONEY_MOVEMENT_TOOLS:
        customer_id = call.input.get("customer_id")
        if customer_id not in state.verified_customers:
            return HookDecision.deny(
                f"KYC prerequisite not met: verify_kyc must succeed for "
                f"{customer_id} before {call.name}."
            )
    return HookDecision.allow()


def _normalize_monetary(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_currency(value).to_serializable()
    if isinstance(value, dict) and set(value) == {"amount", "currency"}:
        return value  # already canonical Money — idempotent
    return value  # numeric amounts and anything else pass through


def _normalize_status_value(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return normalize_status(value)
    return value  # already a label, or a non-code string like "executed" — pass through


def normalization_hook(
    tool_name: str, result: dict[str, Any], state: SessionState
) -> dict[str, Any]:
    """Canonicalize a tool result's heterogeneous formats before the model reads it.

    Recognized key families: monetary (``amount``, ``balance``, ``*_balance``) → :class:`Money`;
    timestamps (``timestamp``, ``date``, ``*_at``) → ISO-8601 UTC; numeric status
    (``status``, ``status_code``) → canonical label. Unrecognized keys pass through unchanged.
    """
    out: dict[str, Any] = {}
    for key, value in result.items():
        if key in _MONETARY_KEYS or key.endswith("_balance"):
            out[key] = _normalize_monetary(value)
        elif key in _TIMESTAMP_KEYS or key.endswith("_at"):
            out[key] = value if value is None else normalize_timestamp(value)
        elif key in _STATUS_KEYS:
            out[key] = _normalize_status_value(value)
        else:
            out[key] = value
    return out


def score_risk_flags(tool_input: dict[str, Any], customer: dict[str, Any]) -> list[str]:
    """A cheap, deterministic risk heuristic — the "$1 guardrail" feeding the compliance layer.

    No trained model: a handful of rules that surface the flags a reviewer needs. The list is
    open/extensible, so escalation is multi-trigger rather than a single hardcoded condition.
    """
    flags: list[str] = []

    amount = coerce_money(tool_input.get("amount")).amount

    if amount > TRANSFER_THRESHOLD:
        flags.append("over_threshold")

    destination_country = tool_input.get("destination_country")
    customer_country = customer.get("country")

    if destination_country and destination_country != customer_country:
        flags.append("cross_border")

    if amount % 1000 == 0:
        flags.append("round_amount")

    status = customer.get("status")
    if status == 2 or status == "dormant":
        flags.append("dormant_account")

    return flags


def build_handoff_summary(tool_input: dict[str, Any], customer: dict[str, Any]) -> HandoffSummary:
    """Compose a self-contained escalation summary from the tool input and customer record alone.

    A compliance officer acts on this without ever seeing the chat transcript.
    """
    amount = coerce_money(tool_input.get("amount"))
    risk_flags = score_risk_flags(tool_input, customer)

    reason = (
        f"Transfer amount {amount.amount} {amount.currency} exceeds "
        f"the threshold of {TRANSFER_THRESHOLD}."
    )

    if "cross_border" in risk_flags:
        reason += (
            f" Destination country {tool_input.get('destination_country')} "
            f"differs from customer country {customer.get('country')}."
        )

    return HandoffSummary(
        customer_id=tool_input.get("customer_id"),
        transaction_type=tool_input.get("transaction_type", "wire_transfer"),
        amount=amount,
        origin_account=tool_input.get("origin_account"),
        destination_account=tool_input.get("destination_account"),
        risk_flags=risk_flags,
        reason_for_escalation=reason,
        recommended_action="Review the transfer and approve or reject it according to compliance policy.",
    )

def make_amount_threshold_hook(load_customer_fn: CustomerLoader) -> Callable[..., HookDecision]:
    """Build a PreToolUse hook that redirects over-threshold transfers to compliance review.

    Parameterized by a customer loader so it can be unit-tested with a fake and wired to the
    real record store in the app.
    """

        def amount_threshold_hook(call: ToolCall, state: SessionState) -> HookDecision:
        if call.name != "initiate_transfer":
            return HookDecision.allow()

        amount = coerce_money(call.input.get("amount"))

        if amount.amount > TRANSFER_THRESHOLD:
            customer_id = call.input.get("customer_id")
            customer = load_customer_fn(customer_id)

            handoff = build_handoff_summary(
                call.input,
                customer,
            )

            return HookDecision.redirect(
                "compliance_review_queue",
                handoff.model_dump(mode="json"),
            )

        return HookDecision.allow()

    return amount_threshold_hook


#: Default interception hook wired to the on-disk customer records.
amount_threshold_hook = make_amount_threshold_hook(load_customer)
