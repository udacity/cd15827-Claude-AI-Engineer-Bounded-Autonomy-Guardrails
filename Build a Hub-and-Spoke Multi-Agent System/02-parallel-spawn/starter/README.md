# Step 2 — Spawn Subagents in Parallel with Scoped Context

## What to build

Wire up the parallel branch of the coordinator so the defect classifier and supplier data subagents run concurrently with per-subagent scoped payloads, then orchestrate the rest of the pipeline.

## TODO locations

- `manufacturing_qc/coordinator.py:Coordinator.run` — replace the stub with the orchestration flow.
- `manufacturing_qc/coordinator.py:Coordinator._spawn_independent` — implement the `asyncio.gather` parallel call with scoped payloads and partial-failure handling.

Search for `# TODO:` to find every spot you need to edit.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_parallel_spawn.py -x
.venv/bin/pytest tests/ -x  # also re-run the step 1 tests
```

All 10 tests in `tests/test_parallel_spawn.py` should pass; the 12 tests from `tests/test_subagent_definitions.py` should still pass.

## What's already provided

Everything from step 1, plus:

- `manufacturing_qc/coordinator.py:_invoke_root_cause` and `_invoke_report` — given infrastructure that you call from `Coordinator.run`.
- `manufacturing_qc/coordinator.py:build_root_cause_payload` — passthrough composer that will be tightened in a later step.
- `tests/test_parallel_spawn.py` — the scoped test suite for this step.
