"""Compliance hooks registered on the :class:`HookEngine`.

Each hook is a deterministic check — the enforcement is programmatic, not prompt-based, so a
zero-tolerance rule (KYC before money movement, no over-threshold transfers) cannot leak.

The KYC prerequisite gate and the PostToolUse normalization hook are complete from Exercises 1
and 2. In this exercise you implement the interception path: ``score_risk_flags``,
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
    # TODO US-03 (LO-5): Build and return a list of string risk flags from a few cheap rules:
    #   - "over_threshold": coerce_money(tool_input.get("amount")).amount > TRANSFER_THRESHOLD
    #   - "cross_border": tool_input["destination_country"] is set and differs from the
    #     customer's "country"
    #   - "round_amount": the amount is an exact multiple of 1000
    #   - "dormant_account": the customer "status" is 2 or "dormant"
    # Keep it open/extensible (append flags), not a single hardcoded condition.
    raise NotImplementedError("TODO US-03: implement the cheap risk scorer")


def build_handoff_summary(tool_input: dict[str, Any], customer: dict[str, Any]) -> HandoffSummary:
    """Compose a self-contained escalation summary from the tool input and customer record alone.

    A compliance officer acts on this without ever seeing the chat transcript.
    """
    # TODO US-03 (LO-5): Build a HandoffSummary whose every field traces to tool_input or the
    # customer record — nothing from a transcript or prior turn. Coerce the amount with
    # coerce_money. Use score_risk_flags(...) for risk_flags. Write a reason_for_escalation that
    # names the amount and the threshold it breached (and the cross-border detail when that flag
    # is present), and a concrete recommended_action. Populate customer_id, transaction_type
    # (default "wire_transfer"), amount, origin_account, and destination_account from tool_input.
    raise NotImplementedError("TODO US-03: build the self-contained handoff summary")


def make_amount_threshold_hook(load_customer_fn: CustomerLoader) -> Callable[..., HookDecision]:
    """Build a PreToolUse hook that redirects over-threshold transfers to compliance review.

    Parameterized by a customer loader so it can be unit-tested with a fake and wired to the
    real record store in the app.
    """

    def amount_threshold_hook(call: ToolCall, state: SessionState) -> HookDecision:
        # TODO US-03 (LO-4): Return HookDecision.allow() for any tool that is not
        # initiate_transfer. For initiate_transfer, coerce the amount with coerce_money; if it is
        # strictly greater than TRANSFER_THRESHOLD, load the customer with load_customer_fn,
        # build a handoff with build_handoff_summary, and return
        # HookDecision.redirect("compliance_review_queue", handoff.model_dump(mode="json")).
        # At or below the threshold, return HookDecision.allow().
        raise NotImplementedError("TODO US-03: implement the interception + redirect hook")

    return amount_threshold_hook


#: Default interception hook wired to the on-disk customer records.
amount_threshold_hook = make_amount_threshold_hook(load_customer)
