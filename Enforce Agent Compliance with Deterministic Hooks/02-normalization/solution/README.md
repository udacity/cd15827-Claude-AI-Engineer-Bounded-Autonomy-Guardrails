# Exercise 2 — Solution

## What this solution contains

- `transaction_agent/money.py` — the four normalizers. `_parse_amount` handles both US
  (`$1,234.56`) and European (`EUR 1.234,56`) separators with the "last separator is the
  decimal" rule and returns exact `Decimal`, never `float`. `normalize_timestamp` and
  `normalize_status` are idempotent and raise typed errors on bad input.
- `transaction_agent/hooks.py` — `normalization_hook` routes each result field to a normalizer
  by key family. `_normalize_status_value` normalizes only numeric codes and passes strings like
  `"executed"` through, so the hook does not crash on a transfer result.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_normalization.py
```

All tests pass (`tests/test_normalization.py` plus the carried-forward
`tests/test_kyc_prerequisite.py`).
