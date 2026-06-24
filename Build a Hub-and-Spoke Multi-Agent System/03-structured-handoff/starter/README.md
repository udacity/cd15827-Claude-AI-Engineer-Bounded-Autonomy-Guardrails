# Exercise 3 — Pass Structured Outputs Between Agents with Pydantic Handoff

## What to build

Tighten the subagent boundaries: validate the root-cause subagent's input against its Pydantic schemas before the call, and add a model validator on `RootCauseHypothesis` that enforces every cited evidence string reference a known input field.

## TODO locations

- `manufacturing_qc/models.py` — define `_ALLOWED_EVIDENCE_FIELDS` and add the `_evidence_must_reference_known_fields` model validator to `RootCauseHypothesis`.
- `manufacturing_qc/coordinator.py:build_root_cause_payload` — add `model_validate` calls so malformed inputs raise `pydantic.ValidationError`.

Search for `# TODO:` to find every spot you need to edit.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_structured_handoff.py -x
.venv/bin/pytest tests/ -x  # full regression
```

All 11 tests in `tests/test_structured_handoff.py` should pass; the 22 tests from Exercises 1-2 should still pass.

## What's already provided

Everything from Exercises 1-2, plus:

- `manufacturing_qc/coordinator.py:_invoke_report` — the structured payload going to the report agent already has the right shape (`defect_id`, `root_cause_hypothesis`, `partial_failures` only).
- `tests/test_structured_handoff.py` — the scoped test suite for this exercise.
