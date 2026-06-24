"""US-03 — Interception hook: block over-threshold transfers + structured handoff."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from transaction_agent.engine import HookEngine
from transaction_agent.hooks import (
    build_handoff_summary,
    kyc_prerequisite_hook,
    make_amount_threshold_hook,
    score_risk_flags,
)
from transaction_agent.models import DecisionType, HandoffSummary, Money, SessionState, ToolCall


def _customer(country: str = "US", status: int = 1) -> dict[str, Any]:
    return {
        "customer_id": "CUST-1",
        "name": "Test Customer",
        "account_number": "ACCT-1",
        "country": country,
        "kyc_status": "verified",
        "status": status,
    }


def _transfer_input(amount: Any, dest_country: str = "US") -> dict[str, Any]:
    return {
        "customer_id": "CUST-1",
        "transaction_type": "wire_transfer",
        "amount": amount,
        "origin_account": "ACCT-1",
        "destination_account": "EXT-9",
        "destination_country": dest_country,
    }


def _loader_for(customer: dict[str, Any]) -> Any:
    return lambda customer_id: customer


def _decide(hook: Any, tool_name: str, tool_input: dict[str, Any]) -> Any:
    return hook(ToolCall(name=tool_name, input=tool_input), SessionState())


# --- AC-03-03: cheap deterministic risk scorer ---


def test_score_risk_flags_over_threshold_cross_border() -> None:
    flags = score_risk_flags(_transfer_input(15000, dest_country="GB"), _customer(country="US"))
    assert "over_threshold" in flags
    assert "cross_border" in flags


def test_score_risk_flags_round_amount_and_dormant() -> None:
    flags = score_risk_flags(_transfer_input(5000), _customer(status=2))
    assert "round_amount" in flags
    assert "dormant_account" in flags
    assert "over_threshold" not in flags  # 5000 is under threshold


def test_score_risk_flags_clean_transfer() -> None:
    flags = score_risk_flags(_transfer_input(4321.50), _customer())
    assert flags == []


# --- AC-03-02: HandoffSummary shape ---


def test_handoff_summary_has_all_fields() -> None:
    handoff = build_handoff_summary(_transfer_input(15000, dest_country="GB"), _customer())
    assert isinstance(handoff, HandoffSummary)
    assert handoff.customer_id == "CUST-1"
    assert handoff.transaction_type == "wire_transfer"
    assert handoff.amount == Money(amount=Decimal("15000"), currency="USD")
    assert handoff.origin_account == "ACCT-1"
    assert handoff.destination_account == "EXT-9"
    assert "over_threshold" in handoff.risk_flags and "cross_border" in handoff.risk_flags
    assert handoff.reason_for_escalation  # non-empty root cause
    assert handoff.recommended_action  # non-empty


# --- AC-03-05: handoff is self-contained (built from tool input + record alone) ---


def test_handoff_self_contained_from_inputs_only() -> None:
    tool_input = _transfer_input(25000, dest_country="GB")
    handoff = build_handoff_summary(tool_input, _customer(country="US"))
    # Every field traces to tool_input or the customer record — nothing from a transcript.
    assert handoff.customer_id == tool_input["customer_id"]
    assert handoff.origin_account == tool_input["origin_account"]
    assert handoff.destination_account == tool_input["destination_account"]
    assert str(handoff.amount.amount) == "25000"
    assert "10000" in handoff.reason_for_escalation  # cites the threshold it breached


# --- AC-03-01 + AC-03-06: the PreToolUse hook redirects / allows by threshold ---


def test_hook_redirects_over_threshold() -> None:
    hook = make_amount_threshold_hook(_loader_for(_customer(country="US")))
    decision = _decide(hook, "initiate_transfer", _transfer_input(15000, "GB"))
    assert decision.decision is DecisionType.REDIRECT
    assert decision.target == "compliance_review_queue"
    assert decision.payload is not None
    assert "over_threshold" in decision.payload["risk_flags"]


def test_hook_allows_at_threshold_and_below() -> None:
    hook = make_amount_threshold_hook(_loader_for(_customer()))
    assert _decide(hook, "initiate_transfer", _transfer_input("$10,000.00")).is_allow
    assert _decide(hook, "initiate_transfer", _transfer_input(5000)).is_allow


def test_hook_boundary_one_cent_over() -> None:
    hook = make_amount_threshold_hook(_loader_for(_customer()))
    at = _decide(hook, "initiate_transfer", _transfer_input("$10,000.00"))
    over = _decide(hook, "initiate_transfer", _transfer_input("$10,000.01"))
    assert at.is_allow
    assert over.decision is DecisionType.REDIRECT


def test_hook_ignores_non_transfer_tools() -> None:
    hook = make_amount_threshold_hook(_loader_for(_customer()))
    assert _decide(hook, "adjust_balance", {"customer_id": "CUST-1"}).is_allow
    assert _decide(hook, "get_customer", {"customer_id": "CUST-1"}).is_allow


# --- AC-03-04: redirected transfer is not executed, is enqueued, returns business error ---


class SpyTool:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"status": "executed"}


def test_engine_redirect_not_executed_enqueued_business_error() -> None:
    engine = HookEngine()
    engine.register_pre(kyc_prerequisite_hook)
    engine.register_pre(make_amount_threshold_hook(_loader_for(_customer(country="US"))))
    state = SessionState(verified_customers={"CUST-1"})  # KYC already done
    spy = SpyTool()
    result = engine.execute_tool_call(
        ToolCall(name="initiate_transfer", input=_transfer_input(15000, "GB")),
        state,
        {"initiate_transfer": spy},
    )
    assert spy.calls == []  # transfer NOT executed
    assert result.is_error is True
    assert result.error_category == "business" and result.is_retryable is False
    assert len(engine.compliance_review_queue) == 1
    assert "over_threshold" in engine.compliance_review_queue[0]["risk_flags"]
