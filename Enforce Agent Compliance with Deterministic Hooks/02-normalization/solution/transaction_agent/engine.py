"""The hook engine: deterministic enforcement around every tool call.

Firing sites (the one ambiguity pinned by spec validation):

* ``PreToolUse`` hooks fire **after** the model emits a tool call and **before** the tool
  function runs; the first non-``allow`` decision short-circuits and the tool never executes.
* ``PostToolUse`` hooks fire **after** the tool function returns and **before** the result is
  handed back to the model, so the model only ever sees canonicalized data.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from transaction_agent.models import (
    ComplianceLog,
    DecisionType,
    HookDecision,
    SessionState,
    ToolCall,
    ToolResult,
)

ToolFn = "object"  # callables returning dict[str, Any]; kept loose so spies/fakes interchange.


class PreToolUseHook(Protocol):
    def __call__(self, call: ToolCall, state: SessionState) -> HookDecision: ...


class PostToolUseHook(Protocol):
    def __call__(
        self, tool_name: str, result: dict[str, Any], state: SessionState
    ) -> dict[str, Any]: ...


class HookEngine:
    """Runs registered hooks around tool dispatch and records every decision."""

    def __init__(self) -> None:
        self._pre: list[PreToolUseHook] = []
        self._post: list[PostToolUseHook] = []
        self.log = ComplianceLog()
        self.queues: dict[str, list[dict[str, Any]]] = {}

    def register_pre(self, hook: PreToolUseHook) -> None:
        self._pre.append(hook)

    def register_post(self, hook: PostToolUseHook) -> None:
        self._post.append(hook)

    @property
    def compliance_review_queue(self) -> list[dict[str, Any]]:
        return self.queues.setdefault("compliance_review_queue", [])

    def run_pre(self, call: ToolCall, state: SessionState) -> HookDecision:
        """Run PreToolUse hooks in registration order, short-circuiting on the first non-allow."""
        for hook in self._pre:
            decision = hook(call, state)
            if not decision.is_allow:
                return decision
        return HookDecision.allow()

    def run_post(
        self, tool_name: str, result: dict[str, Any], state: SessionState
    ) -> dict[str, Any]:
        """Run PostToolUse hooks in order, threading the transformed result through each."""
        for hook in self._post:
            result = hook(tool_name, result, state)
        return result

    def execute_tool_call(
        self,
        call: ToolCall,
        state: SessionState,
        registry: Mapping[str, Any],
    ) -> ToolResult:
        """Enforce hooks, dispatch the tool if allowed, return the result the model will see."""
        customer_id = call.input.get("customer_id")
        decision = self.run_pre(call, state)
        self.log.record(call.name, customer_id, decision.decision, decision.reason)

        if decision.decision is DecisionType.DENY:
            return self._business_error(call.name, decision.reason)

        if decision.decision is DecisionType.REDIRECT:
            target = decision.target or "compliance_review_queue"
            self.queues.setdefault(target, []).append(decision.payload or {})
            return self._business_error(
                call.name,
                f"{decision.reason}: transfer held for human compliance review, not executed.",
            )

        raw = registry[call.name](**call.input)
        result = self.run_post(call.name, raw, state)

        if call.name == "verify_kyc" and result.get("kyc_verified") and result.get("customer_id"):
            state.verified_customers.add(result["customer_id"])

        return ToolResult(tool_name=call.name, content=result, is_error=False)

    @staticmethod
    def _business_error(tool_name: str, reason: str) -> ToolResult:
        return ToolResult(
            tool_name=tool_name,
            content=reason,
            is_error=True,
            error_category="business",
            is_retryable=False,
        )
