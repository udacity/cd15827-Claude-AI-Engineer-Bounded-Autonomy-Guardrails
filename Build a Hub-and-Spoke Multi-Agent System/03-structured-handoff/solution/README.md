# Step 3 — Solution

## What this solution contains

- `manufacturing_qc/models.py` — `_ALLOWED_EVIDENCE_FIELDS` frozenset plus the `RootCauseHypothesis._evidence_must_reference_known_fields` model validator.
- `manufacturing_qc/coordinator.py:build_root_cause_payload` — Pydantic-validates each input before forwarding.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -x
```

All 33 tests pass (12 + 10 + 11).
