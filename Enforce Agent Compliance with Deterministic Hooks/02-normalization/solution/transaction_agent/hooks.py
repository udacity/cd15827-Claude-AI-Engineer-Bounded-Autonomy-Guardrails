"""Compliance hooks registered on the :class:`HookEngine`.

Each hook is a deterministic check — the enforcement is programmatic, not prompt-based, so a
zero-tolerance rule (KYC before money movement) cannot leak.
"""
from __future__ import annotations

from typing import Any

from transaction_agent.models import HookDecision, SessionState, ToolCall
from transaction_agent.money import (
    normalize_currency,
    normalize_status,
    normalize_timestamp,
)

#: Tools that move money and therefore require a completed KYC prerequisite.
MONEY_MOVEMENT_TOOLS = frozenset({"initiate_transfer", "adjust_balance", "resolve_dispute"})

#: Key families the PostToolUse normalization hook recognizes.
_MONETARY_KEYS = frozenset({"amount", "balance"})
_TIMESTAMP_KEYS = frozenset({"timestamp", "date"})
_STATUS_KEYS = frozenset({"status", "status_code"})


def kyc_prerequisite_hook(call: ToolCall, state: SessionState) -> HookDecision:
    """Block money-movement tools until ``verify_kyc`` has recorded a verified id for the customer.

    The exam's canonical prerequisite is "a tool returned a verified customer ID"; the engine
    records that id on a successful ``verify_kyc`` and this hook gates on its presence.
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
