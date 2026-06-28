"""Compliance hooks registered on the :class:`HookEngine`.

Each hook is a deterministic check — the enforcement is programmatic, not prompt-based, so a
zero-tolerance rule (KYC before money movement) cannot leak.

In this step you implement ``kyc_prerequisite_hook``: the programmatic prerequisite that
blocks money-movement tools until ``verify_kyc`` has succeeded for the customer.
"""
from __future__ import annotations

from transaction_agent.models import HookDecision, SessionState, ToolCall

#: Tools that move money and therefore require a completed KYC prerequisite.
MONEY_MOVEMENT_TOOLS = frozenset({"initiate_transfer", "adjust_balance", "resolve_dispute"})


def kyc_prerequisite_hook(call: ToolCall, state: SessionState) -> HookDecision:
    """Block money-movement tools until ``verify_kyc`` has recorded a verified id for the customer.

    The canonical prerequisite is "a tool returned a verified customer ID"; the engine records
    that id on a successful ``verify_kyc`` and this hook gates on its presence.
    """
    # TODO: If call.name is one of MONEY_MOVEMENT_TOOLS, look up the call's
    # customer_id (call.input.get("customer_id")). If that id is NOT in
    # state.verified_customers, return HookDecision.deny(...) with a reason that mentions KYC
    # and names the customer and tool. Otherwise (non-money tool, or KYC already recorded),
    # return HookDecision.allow().
    raise NotImplementedError("TODO US-01: implement the KYC prerequisite gate")
