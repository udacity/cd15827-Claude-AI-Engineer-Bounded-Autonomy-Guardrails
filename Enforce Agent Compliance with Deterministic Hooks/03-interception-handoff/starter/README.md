# Step 3 — Intercept the Risky Transfer and Prove Hooks Beat Prompts

> Picks up from step 2. The KYC gate and normalization hook are in place. This final step
> adds the interception hook, the structured handoff, and the comparison harness that proves
> deterministic enforcement beats even a maximal prompt. When it passes, you have the full
> reference project.

## What to build

1. **Interception + redirect** — a `PreToolUse` hook that blocks any `initiate_transfer` over
   $10,000 and redirects it to the compliance review queue instead of executing it.
2. **A self-contained handoff summary** — a payload a compliance officer can act on without ever
   seeing the chat transcript: every field traced to the tool input or the customer record.
3. **The deterministic-vs-probabilistic switch** — the part of the comparison harness that turns
   the three hooks on (deterministic arm) or leaves them off (prompt-only arm), plus the
   definition of what counts as a policy violation.

## TODO locations

- `transaction_agent/hooks.py` — bodies of `score_risk_flags`, `build_handoff_summary`, and the
  inner `amount_threshold_hook`.
- `transaction_agent/comparison.py` — body of `_build_engine` and the violation predicate in
  `_run_scenario`.

Search for `# TODO:` to find every spot you need to edit.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/                          # full suite (the live test skips without a key)
.venv/bin/transaction-agent compare --offline    # prints hook_violations=0  prompt_violations=4
```

The whole suite should pass. The offline compare prints a table where the deterministic arm
blocks every violation and the prompt-only arm leaks them — the central thesis, made measurable.

## What's already provided

- Everything from steps 1 and 2 (engine, KYC hook, normalization, money, models, tools,
  runner, loop, data).
- `transaction_agent/models.py` — the `HandoffSummary` model.
- `transaction_agent/comparison.py` — the run loop, the report tally, the `PROMPT_ONLY_SYSTEM`
  prompt, the tool-tracking registry, and `process_request`.
- `transaction_agent/__main__.py` — the `transaction-agent run` / `compare` CLI.
- `tests/test_interception_handoff.py` and `tests/test_comparison_and_cli.py` — the scoped tests
  for this step.
