"""The guarded agentic loop.

Termination is driven by ``stop_reason`` — continue while the model returns ``tool_use``, stop
on ``end_turn`` — never by parsing natural-language content and never by an iteration cap as the
primary stop (``max_steps`` is only a runaway backstop). Every tool call is routed through the
:class:`HookEngine`, so enforcement happens between the model's request and the tool executing.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from transaction_agent.engine import HookEngine
from transaction_agent.models import SessionState, ToolCall, ToolResult
from transaction_agent.runner import ModelRunner


@dataclass
class AgentOutcome:
    final_text: str
    executed_tools: list[str] = field(default_factory=list)


def _request_prompt(request: dict[str, Any]) -> str:
    return (
        "Process this customer transaction request using the available tools. "
        "Verify the customer before moving any money.\n\n"
        f"{json.dumps(request, indent=2)}"
    )


def _result_content(result: ToolResult) -> str:
    if result.is_error:
        return str(result.content)
    return json.dumps(result.content)


def run_agent(
    request: dict[str, Any],
    runner: ModelRunner,
    engine: HookEngine,
    registry: Mapping[str, Any],
    state: SessionState,
    *,
    system: str,
    tools: list[dict[str, Any]],
    max_steps: int = 8,
) -> AgentOutcome:
    """Drive the model/tool loop for one request, enforcing hooks around every tool call."""
    messages: list[dict[str, Any]] = [{"role": "user", "content": _request_prompt(request)}]
    executed: list[str] = []
    final_text = ""
    for _ in range(max_steps):
        step = runner.next_step(messages, tools, system)
        if step.stop_reason == "end_turn":
            final_text = step.text
            break
        messages.append({"role": "assistant", "content": step.assistant_content})
        result_blocks: list[dict[str, Any]] = []
        for call in step.tool_calls:
            tool_call = ToolCall(name=call.name, input=call.input)
            result = engine.execute_tool_call(tool_call, state, registry)
            if not result.is_error:
                executed.append(call.name)
            result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": _result_content(result),
                    "is_error": result.is_error,
                }
            )
        messages.append({"role": "user", "content": result_blocks})
    return AgentOutcome(final_text=final_text, executed_tools=executed)
