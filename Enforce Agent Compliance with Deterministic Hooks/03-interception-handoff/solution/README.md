# Exercise 3 — Solution

## What this solution contains

- `transaction_agent/hooks.py` — `score_risk_flags` (the cheap multi-trigger heuristic),
  `build_handoff_summary` (the self-contained escalation payload), and `amount_threshold_hook`
  (the `PreToolUse` interception that redirects over-threshold transfers).
- `transaction_agent/comparison.py` — `_build_engine` registers all three hooks in the
  deterministic arm and nothing in the prompt-only arm, and the violation predicate counts a
  run as a violation when a money-movement tool actually executed.

This is the complete project. `solution(3)` equals the reference repo.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/                          # 50 passed, 1 skipped (live)
.venv/bin/mypy transaction_agent/                # Success
.venv/bin/ruff check transaction_agent/ tests/   # All checks passed
.venv/bin/transaction-agent compare --offline    # hook_violations=0  prompt_violations=4
```

Live arm (optional, needs `ANTHROPIC_API_KEY`):

```bash
.venv/bin/pytest tests/ -m live
.venv/bin/transaction-agent compare
```

## Differences from the reference repo (cleanup-only)

This `solution/` is byte-identical to the reference `transaction_agent/` package, `tests/`,
`data/`, and `pyproject.toml`. The only omissions are non-learner artifacts not shipped into the
course: the repo's top-level `README.md`, the `spec/` directory (PRD, learning objectives,
validation report), and the `notes/` directory (the build-friction log consumed during content
authoring). No source code differs.
