# Step 4 — Add a Bounded Iterative Refinement Loop

## What to build

Add the refinement loop that re-invokes the root cause subagent when the report agent flags a coverage gap, bounded by `max_refinements`. After this step, the multi-agent system is complete.

## TODO locations

- `manufacturing_qc/coordinator.py:Coordinator.__init__` — add a `max_refinements: int = 1` parameter and validate non-negative.
- `manufacturing_qc/coordinator.py:Coordinator.run` — add the bounded refinement while-loop; track `refinement_rounds` in the returned `CorrectiveActionReport`.
- `manufacturing_qc/coordinator.py:Coordinator._invoke_root_cause` — accept an optional `refinement: str | None = None` parameter and include it in the payload when present.
- `manufacturing_qc/coordinator.py:_build_refinement_query` — implement the helper that composes the re-investigation directive from the gap text and the prior hypothesis.

Search for `# TODO:` to find every spot you need to edit.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_refinement_loop.py -x
.venv/bin/pytest tests/ -x  # full regression
```

All 9 unit tests in `tests/test_refinement_loop.py` should pass; the 33 tests from steps 1-3 should still pass. The live API test (1 skipped) runs against the real Anthropic API when you set `ANTHROPIC_API_KEY` and pass `-m live`:

```bash
export ANTHROPIC_API_KEY=...
.venv/bin/pytest tests/ -m live
```

## What's already provided

Everything from steps 1-3, plus:

- `tests/test_refinement_loop.py` — the scoped test suite for this step (8 unit tests + 1 live).
