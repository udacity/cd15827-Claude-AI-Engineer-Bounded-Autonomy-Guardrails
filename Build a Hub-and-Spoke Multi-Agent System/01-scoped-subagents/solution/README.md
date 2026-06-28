# Step 1 — Solution

## What this solution contains

- `manufacturing_qc/subagents.py` — four `SubagentDefinition` instances with goal-oriented `system_prompt`s and scoped `allowed_tools`.
- `manufacturing_qc/coordinator.py` — `SCOPE_COVERAGE` map plus coordinator skeleton.

`Coordinator.run` currently returns a `CorrectiveActionReport` with empty `corrective_actions` (expected at this stage). The full orchestration is added across steps 2-4.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_subagent_definitions.py -x
```

All 12 tests pass.
