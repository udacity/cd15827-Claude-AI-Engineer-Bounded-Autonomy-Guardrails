"""The hook engine: deterministic enforcement around every tool call.

Firing sites (the one ambiguity pinned by spec validation):

* ``PreToolUse`` hooks fire **after** the model emits a tool call and **before** the tool
  function runs; the first non-``allow`` decision short-circuits and the tool never executes.
* ``PostToolUse`` hooks fire **after** the tool function returns and **before** the result is
  handed back to the model, so the model only ever sees canonicalized data.

In this exercise you implement ``run_pre`` and ``execute_tool_call`` — the two methods that
make enforcement happen *in the engine*, before a tool runs. The registration plumbing and the
business-error helper are provided.
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
        # TODO US-01 (LO-2): Run each registered PreToolUse hook (they live in self._pre) in
        # order, calling each with (call, state). The FIRST hook that returns a non-allow
        # decision wins: return it immediately and do not run the remaining hooks. Use
        # HookDecision.is_allow to test a decision. If every hook allows, return
        # HookDecision.allow().
        raise NotImplementedError("TODO US-01: implement PreToolUse short-circuit")

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
        # TODO US-01 (LO-2): Enforcement happens HERE, in the engine, before the tool runs —
        # never inside the tool function. Implement the flow:
        #   1. Read customer_id from call.input (it may be None).
        #   2. decision = self.run_pre(call, state). Record it: self.log.record(call.name,
        #      customer_id, decision.decision, decision.reason).
        #   3. If decision.decision is DecisionType.DENY: return self._business_error(call.name,
        #      decision.reason). The tool function must NOT be called.
        #   4. If decision.decision is DecisionType.REDIRECT: append decision.payload (or {}) to
        #      the queue named by decision.target (default "compliance_review_queue") in
        #      self.queues, then return a self._business_error explaining the call was held for
        #      review. (Redirect is exercised in Exercise 3; wire it now so the engine is whole.)
        #   5. Otherwise the call is allowed: raw = registry[call.name](**call.input); run it
        #      through self.run_post(call.name, raw, state). If this call was a successful
        #      verify_kyc (the result has a truthy "kyc_verified" and a "customer_id"), add that
        #      id to state.verified_customers. Return a non-error ToolResult wrapping the result.
        raise NotImplementedError("TODO US-01: implement engine enforcement + dispatch")

    @staticmethod
    def _business_error(tool_name: str, reason: str) -> ToolResult:
        return ToolResult(
            tool_name=tool_name,
            content=reason,
            is_error=True,
            error_category="business",
            is_retryable=False,
        )
