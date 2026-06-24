# Exercise 1 — Solution

## What this solution contains

- `transaction_agent/hooks.py` — `kyc_prerequisite_hook`: denies money-movement tools for an
  unverified customer, allows everything else.
- `transaction_agent/engine.py` — `HookEngine.run_pre` (short-circuits on the first non-allow
  decision) and `HookEngine.execute_tool_call` (records each decision, returns a structured
  business error for a deny, dispatches the tool when allowed, and records the verified customer
  id on a successful `verify_kyc`).

The engine also wires the redirect branch so it is complete; that branch is first exercised in
Exercise 3.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_kyc_prerequisite.py
```

All tests pass (14).
