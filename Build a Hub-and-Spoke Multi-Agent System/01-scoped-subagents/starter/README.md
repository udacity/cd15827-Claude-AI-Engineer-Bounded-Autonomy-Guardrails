# Step 1 — Define the Coordinator and Four Scoped Subagents

## What to build

Fill in the four `SubagentDefinition` instances and the `SCOPE_COVERAGE` map so the multi-agent system has its hub-and-spoke contracts in place.

## TODO locations

- `manufacturing_qc/subagents.py` — bodies of `DEFECT_CLASSIFIER`, `SUPPLIER_DATA`, `ROOT_CAUSE`, `REPORT` (`system_prompt` and `allowed_tools`).
- `manufacturing_qc/coordinator.py` — the `SCOPE_COVERAGE` dict.

Search for `# TODO:` to find every spot you need to edit.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_subagent_definitions.py -x
```

All 12 tests in `tests/test_subagent_definitions.py` should pass when the four subagent definitions and `SCOPE_COVERAGE` are correctly filled in.

## What's already provided

- `manufacturing_qc/models.py` — Pydantic models for every payload that crosses a subagent boundary.
- `manufacturing_qc/runner.py` — the Anthropic SDK runner that drives subagent calls.
- `manufacturing_qc/tools.py` — the `sqlite_lookup` tool used by the supplier subagent.
- `manufacturing_qc/coordinator.py` — coordinator skeleton plus helper methods (`_invoke_root_cause`, `_invoke_report`, `build_root_cause_payload`); the parallel-spawn logic is added in a later step.
- `manufacturing_qc/__main__.py` — CLI entry point.
- `data/components.sqlite` and `data/defect_reports/D-0001.json` ... `D-0004.json` — sample data.
- `tests/test_subagent_definitions.py` — the scoped test suite for this step.
