"""Anthropic SDK runner for subagents.

Each subagent invocation:
1. Builds a tool list — one schema-bound "emit" tool whose input_schema is the
   subagent's output Pydantic schema, plus any external tools in `allowed_tools`.
2. Sends the scoped payload as a single user message; the subagent system prompt
   stays consistent across turns.
3. Loops over the response: executes any `tool_use` blocks for external tools
   (e.g., sqlite_lookup) via the injected handlers and feeds results back. The
   loop terminates when the subagent calls the emit tool — its `input` is parsed
   into the output schema and returned.

Anthropic API errors are not caught here — the coordinator's partial-failure
handling treats raised exceptions as the failure signal.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from anthropic import Anthropic
from pydantic import BaseModel

from manufacturing_qc.subagents import REPORT, SubagentDefinition
from manufacturing_qc.tools import SQLITE_LOOKUP_TOOL_SCHEMA

ToolHandler = Callable[[Mapping[str, Any]], BaseModel | None]


class AnthropicSubagentRunner:
    """Production runner backed by the Anthropic Messages API.

    `tool_handlers` maps each external tool name (currently just `sqlite_lookup`)
    to a synchronous callable that takes the tool's input dict and returns a
    Pydantic model (or None). Handlers are JSON-serialized via `model_dump_json`
    before being fed back to the model.
    """

    def __init__(
        self,
        model: str = "claude-haiku-4-5",
        tool_handlers: Mapping[str, ToolHandler] | None = None,
        max_tool_iterations: int = 6,
    ) -> None:
        self._client = Anthropic()
        self._model = model
        self._tool_handlers = dict(tool_handlers or {})
        self._max_tool_iterations = max_tool_iterations

    async def run(
        self, subagent: SubagentDefinition, payload: Mapping[str, object]
    ) -> BaseModel:
        emit_name = _emit_tool_name(subagent)
        tools = self._build_tools(subagent, emit_name)
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": json.dumps(dict(payload), default=str)}
        ]

        for _ in range(self._max_tool_iterations):
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=subagent.system_prompt,
                tools=tools,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            )

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                raise RuntimeError(
                    f"{subagent.name} returned no tool_use blocks "
                    f"(stop_reason={response.stop_reason}); expected emit tool"
                )

            messages.append({"role": "assistant", "content": response.content})

            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                if tu.name == emit_name:
                    return subagent.output_schema.model_validate(tu.input)
                handler = self._tool_handlers.get(tu.name)
                if handler is None:
                    raise RuntimeError(
                        f"{subagent.name} called unsupported tool {tu.name!r}"
                    )
                result = handler(dict(tu.input))
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": (
                            result.model_dump_json() if result is not None else "null"
                        ),
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        raise RuntimeError(
            f"{subagent.name} exceeded {self._max_tool_iterations} tool iterations "
            "without calling the emit tool"
        )

    @staticmethod
    def _build_tools(
        subagent: SubagentDefinition, emit_name: str
    ) -> list[dict[str, object]]:
        tools: list[dict[str, object]] = [
            {
                "name": emit_name,
                "description": (
                    f"Emit the final {subagent.output_schema.__name__} for this subagent. "
                    "Call this once you have the complete structured output."
                ),
                "input_schema": subagent.output_schema.model_json_schema(),
            }
        ]
        if "sqlite_lookup" in subagent.allowed_tools:
            tools.append(SQLITE_LOOKUP_TOOL_SCHEMA)
        return tools


def _emit_tool_name(subagent: SubagentDefinition) -> str:
    """The report subagent's emit tool is conventionally named `emit_report`;
    other subagents use a schema-derived name."""
    if subagent is REPORT or "emit_report" in subagent.allowed_tools:
        return "emit_report"
    return f"emit_{subagent.output_schema.__name__.lower()}"
