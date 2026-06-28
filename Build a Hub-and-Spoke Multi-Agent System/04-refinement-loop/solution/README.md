# Step 4 — Solution

## What this solution contains

- `manufacturing_qc/coordinator.py:Coordinator.__init__` — `max_refinements: int = 1` with non-negative validation.
- `manufacturing_qc/coordinator.py:Coordinator.run` — bounded refinement while-loop driven by `subagent_report.coverage_gap`; tracks `refinement_rounds`.
- `manufacturing_qc/coordinator.py:Coordinator._invoke_root_cause` — accepts `refinement: str | None`; adds it to the payload when present.
- `manufacturing_qc/coordinator.py:_build_refinement_query` — composes the re-investigation directive: `"Re-investigate: <gap>. Prior hypothesis: <summary>"`.
- `manufacturing_qc/__main__.py` — adds a `--max-refinements` CLI flag.

This is the complete project. The CLI now runs end-to-end against the real Anthropic API and produces a corrective-action report.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -x       # 42 unit tests (1 live skipped without ANTHROPIC_API_KEY)
```

For the live API test:

```bash
export ANTHROPIC_API_KEY=...
.venv/bin/pytest tests/ -m live
.venv/bin/manufacturing-qc run data/defect_reports/D-0001.json
```
