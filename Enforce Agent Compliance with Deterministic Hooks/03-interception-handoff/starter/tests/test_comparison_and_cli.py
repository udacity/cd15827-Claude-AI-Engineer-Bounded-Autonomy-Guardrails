"""US-04 — Enforcement-vs-prompt comparison harness + CLI + loop lifecycle."""
from __future__ import annotations

import json
import os
from typing import Any

import pytest

from transaction_agent.__main__ import main
from transaction_agent.comparison import run_comparison
from transaction_agent.config import DATA_DIR
from transaction_agent.engine import HookEngine
from transaction_agent.loop import run_agent
from transaction_agent.models import SessionState
from transaction_agent.runner import ModelStep, ToolCallRequest, ViolationAttemptRunner
from transaction_agent.tools import build_registry, load_scenarios, tool_schemas


def _offline_factory(request: dict[str, Any], arm: str) -> ViolationAttemptRunner:
    return ViolationAttemptRunner(request)


# --- AC-04-01 + AC-04-02 + AC-04-03: deterministic comparison ---


def test_hooks_block_every_violation_deterministically() -> None:
    scenarios = load_scenarios()
    report = run_comparison(scenarios, _offline_factory)
    # The scripted runner attempts the violation in every scenario, in both arms.
    assert report.hook_violations == 0  # hooks block 100% by construction
    assert report.prompt_violations > 0  # prompt-only arm lets attempts through
    assert report.hook_violations <= report.prompt_violations
    assert report.total_runs == len(scenarios) * 2  # 2 arms per scenario


def test_report_has_per_scenario_breakdown() -> None:
    scenarios = load_scenarios()
    report = run_comparison(scenarios, _offline_factory)
    arms = {(r.name, r.arm) for r in report.results}
    for scenario in scenarios:
        assert (scenario["name"], "hooks") in arms
        assert (scenario["name"], "prompt_only") in arms
    # Every hooks-arm result is a non-violation; outcome is denied or redirected, never executed.
    for r in report.results:
        if r.arm == "hooks":
            assert not r.violated
            assert r.outcome in {"denied", "redirected"}


def test_runs_per_scenario_multiplies_total() -> None:
    scenarios = load_scenarios()
    report = run_comparison(scenarios, _offline_factory, runs_per_scenario=3)
    assert report.total_runs == len(scenarios) * 2 * 3
    assert report.hook_violations == 0


# --- loop lifecycle: terminates on stop_reason == "end_turn" ---


class _ScriptedSteps:
    def __init__(self, steps: list[ModelStep]) -> None:
        self._steps = steps
        self._i = 0

    def next_step(self, messages: Any, tools: Any, system: str) -> ModelStep:
        step = self._steps[self._i]
        self._i += 1
        return step


def test_loop_terminates_on_end_turn() -> None:
    runner = _ScriptedSteps([ModelStep("end_turn", text="nothing to do")])
    outcome = run_agent(
        {"customer_id": "C"},
        runner,
        HookEngine(),
        build_registry(),
        SessionState(),
        system="s",
        tools=tool_schemas(),
    )
    assert outcome.final_text == "nothing to do"
    assert outcome.executed_tools == []


def test_loop_runs_tool_then_ends() -> None:
    call = ToolCallRequest("id1", "get_customer", {"customer_id": "CUST-10293"})
    tool_use = ModelStep(
        "tool_use",
        tool_calls=[call],
        assistant_content=[
            {"type": "tool_use", "id": "id1", "name": "get_customer", "input": call.input}
        ],
    )
    runner = _ScriptedSteps([tool_use, ModelStep("end_turn", text="done")])
    outcome = run_agent(
        {"customer_id": "CUST-10293"},
        runner,
        HookEngine(),
        build_registry(),
        SessionState(),
        system="s",
        tools=tool_schemas(),
    )
    assert outcome.final_text == "done"
    assert outcome.executed_tools == ["get_customer"]


# --- AC-04-05: CLI ---


def test_cli_compare_offline(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["compare", "--offline"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "hook_violations=0" in out
    assert "prompt_violations=" in out


def test_cli_run_offline_redirected(capsys: pytest.CaptureFixture[str]) -> None:
    # REQ-002: verified customer, $15,000 transfer -> over threshold -> redirected.
    request_path = DATA_DIR / "requests" / "req_002.json"
    rc = main(["run", str(request_path), "--offline"])
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["outcome"] == "redirected"


def test_cli_run_offline_denied(capsys: pytest.CaptureFixture[str]) -> None:
    # REQ-004: KYC pending -> money movement denied.
    request_path = DATA_DIR / "requests" / "req_004.json"
    rc = main(["run", str(request_path), "--offline"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "denied"


def test_cli_requires_key_without_offline(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rc = main(["compare"])
    assert rc == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


# --- AC-04-04: live arm (skipped without a key) ---


@pytest.mark.live
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"), reason="live test needs ANTHROPIC_API_KEY"
)
def test_live_hooks_zero_violations() -> None:
    from transaction_agent.runner import AnthropicRunner

    def factory(request: dict[str, Any], arm: str) -> AnthropicRunner:
        return AnthropicRunner()

    scenarios = load_scenarios()[:2]
    report = run_comparison(scenarios, factory)
    assert report.hook_violations == 0
    assert report.total_runs == len(scenarios) * 2
