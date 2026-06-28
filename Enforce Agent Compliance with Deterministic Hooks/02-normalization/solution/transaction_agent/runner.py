"""Model runners — the loop talks to the model through a single Protocol.

The real :class:`AnthropicRunner` makes live API calls; :class:`ViolationAttemptRunner` is a
scripted test double for the *loop* (not a fake HTTP response) that always tries to move money,
so the deterministic-enforcement guarantee can be proven without the network.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from transaction_agent.config import DEFAULT_MODEL


@dataclass
class ToolCallRequest:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ModelStep:
    """One turn from the model: tool calls (``tool_use``) or a final answer (``end_turn``)."""

    stop_reason: str
    text: str = ""
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    assistant_content: list[dict[str, Any]] = field(default_factory=list)


Messages = list[dict[str, Any]]
Tools = list[dict[str, Any]]


class ModelRunner(Protocol):
    def next_step(self, messages: Messages, tools: Tools, system: str) -> ModelStep: ...


def _tool_use_block(call: ToolCallRequest) -> dict[str, Any]:
    return {"type": "tool_use", "id": call.id, "name": call.name, "input": call.input}


_MONEY_TOOL_FOR_TYPE = {
    "wire_transfer": "initiate_transfer",
    "account_adjustment": "adjust_balance",
    "dispute_resolution": "resolve_dispute",
}


class ViolationAttemptRunner:
    """Scripted runner that attempts the money movement regardless of policy.

    Plan: call ``verify_kyc`` (its result is honest — it only succeeds for verified customers),
    then attempt the money-movement tool, then end. With hooks active the attempt is blocked
    deterministically; with hooks off it executes — which is exactly the contrast this harness measures.
    """

    def __init__(self, request: dict[str, Any]) -> None:
        self.request = request
        self._step = 0

    def next_step(self, messages: Messages, tools: Tools, system: str) -> ModelStep:
        customer_id = self.request["customer_id"]
        if self._step == 0:
            self._step = 1
            call = ToolCallRequest("call_kyc", "verify_kyc", {"customer_id": customer_id})
            return ModelStep(
                "tool_use", tool_calls=[call], assistant_content=[_tool_use_block(call)]
            )
        if self._step == 1:
            self._step = 2
            call = self._money_call()
            return ModelStep(
                "tool_use", tool_calls=[call], assistant_content=[_tool_use_block(call)]
            )
        return ModelStep("end_turn", text="Transaction request processing complete.")

    def _money_call(self) -> ToolCallRequest:
        txn_type = self.request.get("transaction_type", "")
        tool = _MONEY_TOOL_FOR_TYPE.get(txn_type, "initiate_transfer")
        if tool == "initiate_transfer":
            payload = {
                "customer_id": self.request["customer_id"],
                "amount": self.request["amount"],
                "origin_account": self.request["origin_account"],
                "destination_account": self.request["destination_account"],
                "destination_country": self.request.get("destination_country"),
            }
        elif tool == "adjust_balance":
            payload = {"customer_id": self.request["customer_id"], "amount": self.request["amount"]}
        else:
            payload = {"customer_id": self.request["customer_id"]}
        return ToolCallRequest("call_money", tool, payload)


class AnthropicRunner:
    """Live runner over the Anthropic Messages API."""

    def __init__(
        self, model: str = DEFAULT_MODEL, max_tokens: int = 1024, client: Any | None = None
    ) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self._client: Any = client
        self._model = model
        self._max_tokens = max_tokens

    def next_step(self, messages: Messages, tools: Tools, system: str) -> ModelStep:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=0,
            system=system,
            tools=tools,
            messages=messages,
        )
        blocks: list[Any] = list(response.content)
        assistant_content = [block.model_dump() for block in blocks]
        if response.stop_reason == "tool_use":
            calls = [
                ToolCallRequest(id=block.id, name=block.name, input=dict(block.input))
                for block in blocks
                if block.type == "tool_use"
            ]
            return ModelStep("tool_use", tool_calls=calls, assistant_content=assistant_content)
        text = "".join(block.text for block in blocks if block.type == "text")
        return ModelStep("end_turn", text=text, assistant_content=assistant_content)
