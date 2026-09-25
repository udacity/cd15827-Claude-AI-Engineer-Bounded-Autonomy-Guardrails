"""Compliance hooks registered on the :class:`HookEngine`.

Each hook is a deterministic check — the enforcement is programmatic, not prompt-based, so a
zero-tolerance rule (KYC before money movement) cannot leak.

The KYC prerequisite hook is already complete from step 1. In this step you implement
``normalization_hook`` (a PostToolUse hook) and its two field-level helpers.
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
        return value

    return value


def _normalize_status_value(value: Any) -> Any:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return normalize_status(value)

    if isinstance(value, str) and value.isdigit():
        return normalize_status(value)

    return value


def normalization_hook(
    tool_name: str, result: dict[str, Any], state: SessionState
) -> dict[str, Any]:
    """Canonicalize a tool result's heterogeneous formats before the model reads it.

    Recognized key families: monetary (``amount``, ``balance``, ``*_balance``) → :class:`Money`;
    timestamps (``timestamp``, ``date``, ``*_at``) → ISO-8601 UTC; numeric status
    (``status``, ``status_code``) → canonical label. Unrecognized keys pass through unchanged.
    """
    normalized: dict[str, Any] = {}

    for key, value in result.items():
        if key in _MONETARY_KEYS or key.endswith("_balance"):
            normalized[key] = _normalize_monetary(value)

        elif key in _TIMESTAMP_KEYS or key.endswith("_at"):
            if value is None:
                normalized[key] = None
            else:
                normalized[key] = normalize_timestamp(value)

        elif key in _STATUS_KEYS:
            normalized[key] = _normalize_status_value(value)

        else:
            normalized[key] = value

    return normalized
