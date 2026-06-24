# Exercise 1 — Enforce a KYC Prerequisite in Code, Not the Prompt

## What to build

A hook engine that enforces a **programmatic** compliance prerequisite: no money-movement tool
(`initiate_transfer`, `adjust_balance`, `resolve_dispute`) may run for a customer until
`verify_kyc` has succeeded for that customer. The guarantee comes from code in the engine, not
from a sentence in a prompt.

## TODO locations

- `transaction_agent/hooks.py` — body of `kyc_prerequisite_hook`.
- `transaction_agent/engine.py` — bodies of `HookEngine.run_pre` and `HookEngine.execute_tool_call`.

Search for `# TODO:` to find every spot you need to edit.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_kyc_prerequisite.py
```

All tests in `tests/test_kyc_prerequisite.py` should pass once the hook and the two engine
methods are implemented. The key test (`test_denied_call_not_executed_and_returns_business_error`)
asserts the tool function is **never invoked** when KYC is missing — proof the engine, not the
tool, is the control.

## What's already provided

- `transaction_agent/models.py` — `HookDecision` (allow/deny/redirect), `ToolCall`, `ToolResult`,
  `SessionState`, `ComplianceLog`, and the other typed payloads.
- `transaction_agent/tools.py` — the simulated banking tools and their JSON-Schema definitions.
- `transaction_agent/runner.py` — the Anthropic SDK runner and the scripted test runner.
- `transaction_agent/loop.py` — the `stop_reason`-driven agentic loop that routes every tool
  call through the engine.
- `transaction_agent/engine.py` — the registration plumbing (`register_pre`/`register_post`,
  `run_post`, the queue property) and the `_business_error` helper.
- `data/` — customer records and transaction requests.
- `tests/test_kyc_prerequisite.py` — the scoped test suite for this exercise.
