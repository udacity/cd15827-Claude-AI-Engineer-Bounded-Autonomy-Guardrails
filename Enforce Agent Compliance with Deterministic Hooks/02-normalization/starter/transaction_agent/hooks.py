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
    # TODO: If value is a currency string, return
    # normalize_currency(value).to_serializable() (the canonical {"amount", "currency"} dict).
    # If value is already a canonical Money dict (its keys are exactly {"amount", "currency"}),
    # return it unchanged so the hook is idempotent. Numeric amounts and anything else pass
    # through untouched (a bare number is not a currency string and must not be coerced here).
    raise NotImplementedError("TODO US-02: normalize a monetary field value")


def _normalize_status_value(value: Any) -> Any:
    # TODO: Normalize ONLY numeric status codes; pass strings through. Watch the
    # sharp edge: get_customer returns a numeric status (1/2/3), but initiate_transfer returns
    # status="executed". A hook that maps every status key crashes on "executed". So: leave bool
    # untouched; for an int (or an all-digits string) call normalize_status(value); otherwise
    # (an already-canonical label or a non-code string like "executed") return value unchanged.
    raise NotImplementedError("TODO US-02: normalize a status field value")


def normalization_hook(
    tool_name: str, result: dict[str, Any], state: SessionState
) -> dict[str, Any]:
    """Canonicalize a tool result's heterogeneous formats before the model reads it.

    Recognized key families: monetary (``amount``, ``balance``, ``*_balance``) → :class:`Money`;
    timestamps (``timestamp``, ``date``, ``*_at``) → ISO-8601 UTC; numeric status
    (``status``, ``status_code``) → canonical label. Unrecognized keys pass through unchanged.
    """
    # TODO: Build and return a NEW dict. For each key/value in result, route by key
    # family: monetary keys (in _MONETARY_KEYS or ending in "_balance") -> _normalize_monetary;
    # timestamp keys (in _TIMESTAMP_KEYS or ending in "_at") -> normalize_timestamp, but pass a
    # None value through untouched; status keys (in _STATUS_KEYS) -> _normalize_status_value;
    # any other key -> copy the value unchanged.
    raise NotImplementedError("TODO US-02: route each field to its normalizer by key family")
