"""Compliance hooks registered on the :class:`HookEngine`.

Each hook is a deterministic check — the enforcement is programmatic, not prompt-based, so a
zero-tolerance rule (KYC before money movement) cannot leak.
"""
from __future__ import annotations

from transaction_agent.models import HookDecision, SessionState, ToolCall

#: Tools that move money and therefore require a completed KYC prerequisite.
MONEY_MOVEMENT_TOOLS = frozenset({"initiate_transfer", "adjust_balance", "resolve_dispute"})


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
