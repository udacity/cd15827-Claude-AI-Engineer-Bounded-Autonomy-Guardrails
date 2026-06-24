"""Typed payloads that cross hook and tool boundaries.

Every value exchanged between the model loop, the hook engine, and the tools is one of
these models — no untyped dicts cross a boundary except a tool's raw result dict, which the
PostToolUse normalization hook canonicalizes in place.
"""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    """A model-requested tool invocation, as seen by PreToolUse hooks."""

    name: str
    input: dict[str, Any] = Field(default_factory=dict)


class DecisionType(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REDIRECT = "redirect"


class HookDecision(BaseModel):
    """The verdict a PreToolUse hook returns for a tool call.

    ``redirect`` is kept distinct from ``deny`` because the downstream effect differs: a deny
    feeds a business error back to the model, while a redirect additionally enqueues a payload
    (a :class:`HandoffSummary`) on a named queue.
    """

    decision: DecisionType
    reason: str = ""
    target: str | None = None
    payload: dict[str, Any] | None = None

    @classmethod
    def allow(cls) -> HookDecision:
        return cls(decision=DecisionType.ALLOW)

    @classmethod
    def deny(cls, reason: str) -> HookDecision:
        return cls(decision=DecisionType.DENY, reason=reason)

    @classmethod
    def redirect(cls, target: str, payload: dict[str, Any]) -> HookDecision:
        return cls(
            decision=DecisionType.REDIRECT,
            target=target,
            payload=payload,
            reason=f"redirected to {target}",
        )

    @property
    def is_allow(self) -> bool:
        return self.decision is DecisionType.ALLOW


class ToolResult(BaseModel):
    """The result fed back to the model after a tool call resolves.

    Blocked calls (deny/redirect) carry the exam's structured-error taxonomy so the model
    treats them as terminal business errors rather than retrying or claiming success.
    """

    tool_name: str
    content: Any
    is_error: bool = False
    error_category: str | None = None
    is_retryable: bool | None = None


class SessionState(BaseModel):
    """Mutable per-session enforcement state."""

    verified_customers: set[str] = Field(default_factory=set)


class ComplianceLogEntry(BaseModel):
    tool_name: str
    customer_id: str | None
    decision: DecisionType
    reason: str


class ComplianceLog(BaseModel):
    """An inspectable audit trail of every enforcement decision."""

    entries: list[ComplianceLogEntry] = Field(default_factory=list)

    def record(
        self, tool_name: str, customer_id: str | None, decision: DecisionType, reason: str
    ) -> None:
        self.entries.append(
            ComplianceLogEntry(
                tool_name=tool_name, customer_id=customer_id, decision=decision, reason=reason
            )
        )


class Money(BaseModel):
    """An exact monetary amount: ``Decimal`` (never ``float``) plus an ISO-4217 currency code."""

    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency: str

    def to_serializable(self) -> dict[str, str]:
        return {"amount": str(self.amount), "currency": self.currency}


class HandoffSummary(BaseModel):
    """Self-contained escalation payload for a human compliance officer (no transcript access)."""

    customer_id: str
    transaction_type: str
    amount: Money
    origin_account: str
    destination_account: str
    risk_flags: list[str]
    reason_for_escalation: str
    recommended_action: str


class ScenarioResult(BaseModel):
    name: str
    arm: str  # "hooks" or "prompt_only"
    violated: bool
    outcome: str  # executed | denied | redirected


class ComparisonReport(BaseModel):
    """Outcome of the enforcement-vs-prompt comparison harness."""

    total_runs: int
    hook_violations: int
    prompt_violations: int
    results: list[ScenarioResult] = Field(default_factory=list)
