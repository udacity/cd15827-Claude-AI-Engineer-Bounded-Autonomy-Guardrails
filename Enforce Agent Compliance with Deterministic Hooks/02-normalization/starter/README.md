# Step 2 — Normalize Messy Tool Output Before the Model Reads It

> Picks up from step 1. Your KYC gate and hook engine are in place. This step adds the
> `PostToolUse` side of the engine: a hook that canonicalizes heterogeneous tool output before
> the model ever sees it.

## What to build

A `PostToolUse` normalization hook (and the format normalizers it relies on) that turns the
messy data real banking tools emit into one canonical representation: currency strings in any
locale into exact `Decimal` `Money`, Unix-epoch timestamps into ISO-8601 UTC, and numeric status
codes into labels — while leaving everything else untouched.

## TODO locations

- `transaction_agent/money.py` — bodies of `_parse_amount`, `normalize_currency`,
  `normalize_timestamp`, `normalize_status`.
- `transaction_agent/hooks.py` — bodies of `normalization_hook`, `_normalize_monetary`,
  `_normalize_status_value`.

Search for `# TODO:` to find every spot you need to edit. Two of the TODOs flag sharp edges that
will bite a naive implementation (European currency separators, and the `status` key collision).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_normalization.py
```

All tests in `tests/test_normalization.py` should pass. `tests/test_kyc_prerequisite.py` from
Step 1 still passes too.

## What's already provided

- Everything from step 1 (engine, KYC hook, models, tools, runner, loop, data).
- `transaction_agent/money.py` — the typed parse-error classes, the currency lookup tables, the
  `_detect_currency` helper, and `coerce_money`.
- `tests/test_normalization.py` — the scoped test suite for this step.
