# Exercise 2 — Solution

## What this solution contains

- `manufacturing_qc/coordinator.py:Coordinator.run` — orchestrates the four-subagent pipeline.
- `manufacturing_qc/coordinator.py:Coordinator._spawn_independent` — parallel classifier+supplier call via `asyncio.gather(..., return_exceptions=True)` with per-subagent scoped payloads and partial-failure handling.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -x
```

All 22 tests pass (12 from Exercise 1 + 10 from Exercise 2).
