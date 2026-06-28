"""Hook engine + programmatic KYC prerequisite gate."""
from __future__ import annotations

from typing import Any

import pytest

from transaction_agent.engine import HookEngine
from transaction_agent.hooks import kyc_prerequisite_hook
from transaction_agent.models import DecisionType, HookDecision, SessionState, ToolCall


class SpyTool:
    """Records whether it was invoked — proves the engine, not the tool, enforces the gate."""

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return self.result


# --- HookDecision variants + engine short-circuits on first non-allow ---


def test_hook_decision_variants() -> None:
    assert HookDecision.allow().decision is DecisionType.ALLOW
    assert HookDecision.allow().is_allow is True
    deny = HookDecision.deny("nope")
    assert deny.decision is DecisionType.DENY and deny.reason == "nope" and deny.is_allow is False
    red = HookDecision.redirect("compliance_review_queue", {"k": "v"})
    assert red.decision is DecisionType.REDIRECT
    assert red.target == "compliance_review_queue" and red.payload == {"k": "v"}


def test_engine_short_circuits_on_first_deny() -> None:
    fired: list[str] = []

    def hook_a(call: ToolCall, state: SessionState) -> HookDecision:
        fired.append("a")
        return HookDecision.deny("blocked by a")

    def hook_b(call: ToolCall, state: SessionState) -> HookDecision:
        fired.append("b")
        return HookDecision.allow()

    engine = HookEngine()
    engine.register_pre(hook_a)
    engine.register_pre(hook_b)
    call = ToolCall(name="initiate_transfer", input={"customer_id": "C1"})
    decision = engine.run_pre(call, SessionState())
    assert decision.decision is DecisionType.DENY
    assert fired == ["a"]  # hook_b never ran


# --- kyc hook deny/allow per tool + verified state ---


@pytest.mark.parametrize("tool", ["initiate_transfer", "adjust_balance", "resolve_dispute"])
def test_money_movement_denied_without_kyc(tool: str) -> None:
    call = ToolCall(name=tool, input={"customer_id": "C1"})
    decision = kyc_prerequisite_hook(call, SessionState())
    assert decision.decision is DecisionType.DENY
    assert "kyc" in decision.reason.lower()


@pytest.mark.parametrize("tool", ["initiate_transfer", "adjust_balance", "resolve_dispute"])
def test_money_movement_allowed_after_kyc(tool: str) -> None:
    state = SessionState(verified_customers={"C1"})
    decision = kyc_prerequisite_hook(ToolCall(name=tool, input={"customer_id": "C1"}), state)
    assert decision.is_allow


@pytest.mark.parametrize("tool", ["verify_kyc", "get_customer"])
def test_non_money_tools_always_allowed(tool: str) -> None:
    call = ToolCall(name=tool, input={"customer_id": "C1"})
    decision = kyc_prerequisite_hook(call, SessionState())
    assert decision.is_allow


# --- gate enforced by engine; verify_kyc records verified id ---


def test_denied_call_not_executed_and_returns_business_error() -> None:
    engine = HookEngine()
    engine.register_pre(kyc_prerequisite_hook)
    spy = SpyTool({"status": "executed"})
    state = SessionState()
    result = engine.execute_tool_call(
        ToolCall(name="initiate_transfer", input={"customer_id": "C1", "amount": 50}),
        state,
        {"initiate_transfer": spy},
    )
    assert spy.calls == []  # tool function NEVER invoked
    assert result.is_error is True
    assert result.error_category == "business"
    assert result.is_retryable is False


def test_verify_kyc_success_records_id_then_transfer_allowed() -> None:
    engine = HookEngine()
    engine.register_pre(kyc_prerequisite_hook)
    state = SessionState()
    verify = SpyTool({"customer_id": "C1", "kyc_verified": True, "verified_at": 1715212800})
    transfer = SpyTool({"status": "executed", "transaction_id": "TXN-1"})
    registry = {"verify_kyc": verify, "initiate_transfer": transfer}

    transfer_call = ToolCall(name="initiate_transfer", input={"customer_id": "C1", "amount": 50})

    # Before KYC: transfer is denied, not executed.
    blocked = engine.execute_tool_call(transfer_call, state, registry)
    assert blocked.is_error and transfer.calls == []

    # Run verify_kyc -> engine records the verified id.
    verify_call = ToolCall(name="verify_kyc", input={"customer_id": "C1"})
    engine.execute_tool_call(verify_call, state, registry)
    assert "C1" in state.verified_customers

    # Now the transfer is allowed and the tool function runs.
    ok = engine.execute_tool_call(transfer_call, state, registry)
    assert ok.is_error is False
    assert transfer.calls == [{"customer_id": "C1", "amount": 50}]


def test_verify_kyc_failure_does_not_record() -> None:
    engine = HookEngine()
    engine.register_pre(kyc_prerequisite_hook)
    state = SessionState()
    verify = SpyTool({"customer_id": "C9", "kyc_verified": False, "verified_at": None})
    call = ToolCall(name="verify_kyc", input={"customer_id": "C9"})
    engine.execute_tool_call(call, state, {"verify_kyc": verify})
    assert "C9" not in state.verified_customers


# --- ComplianceLog records every decision ---


def test_compliance_log_records_denied_transfer() -> None:
    engine = HookEngine()
    engine.register_pre(kyc_prerequisite_hook)
    state = SessionState()
    engine.execute_tool_call(
        ToolCall(name="initiate_transfer", input={"customer_id": "C1", "amount": 50}),
        state,
        {"initiate_transfer": SpyTool({})},
    )
    denies = [e for e in engine.log.entries if e.decision is DecisionType.DENY]
    assert len(denies) == 1
    assert denies[0].tool_name == "initiate_transfer"
    assert denies[0].customer_id == "C1"
    assert "kyc" in denies[0].reason.lower()
