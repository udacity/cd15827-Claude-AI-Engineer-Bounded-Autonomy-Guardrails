# AI Engineer — Bounded Autonomy & Guardrails

This repo is the source of truth for the exercises in this course. Each exercise is a
self-contained Python project that builds, step by step, toward a complete reference
implementation. Every step ships a `starter/` (with `# TODO:` markers) and a matching
`solution/`, and is verified by a scoped `pytest` suite.

The two exercise projects show two complementary ways to keep an autonomous agent inside
its lane: **structural** boundaries between cooperating agents, and **deterministic** code
that enforces compliance regardless of the prompt.

## Folder Structure

The repo contains one folder per exercise project. Each project folder contains numbered
build steps, and each step contains a `starter/` and a `solution/`:

```bash
Exercise Project Name/
├── 01-step-name/
│   ├── starter/      # code with # TODO: markers + a step README.md
│   └── solution/     # completed reference implementation
├── 02-step-name/
│   ├── starter/
│   └── solution/
└── ...
```

Each `starter/` and `solution/` is an installable Python package (`pyproject.toml`) with its
own `data/`, source package, `tests/`, and a `README.md` describing what to build, where the
TODOs are, how to set up, and how to verify.

> The step numbers (`01-`, `02-`, …) denote build order *within a single project* — each step
> picks up where the previous one left off. They are not a fixed course ordering.

## Exercises

### [Build a Hub-and-Spoke Multi-Agent System](Build%20a%20Hub-and-Spoke%20Multi-Agent%20System/)

A manufacturing QC pipeline (`manufacturing_qc`) where a coordinator fans work out to four
scoped subagents and refines the result. Built over four steps:

1. **[01-scoped-subagents](Build%20a%20Hub-and-Spoke%20Multi-Agent%20System/01-scoped-subagents/)** — Define the coordinator and four scoped subagents (system prompts, allowed tools, and the scope-coverage map).
2. **[02-parallel-spawn](Build%20a%20Hub-and-Spoke%20Multi-Agent%20System/02-parallel-spawn/)** — Spawn the independent subagents concurrently with `asyncio.gather` and per-subagent scoped context, with partial-failure handling.
3. **[03-structured-handoff](Build%20a%20Hub-and-Spoke%20Multi-Agent%20System/03-structured-handoff/)** — Pass validated Pydantic payloads across agent boundaries, including an evidence-must-reference-known-fields model validator.
4. **[04-refinement-loop](Build%20a%20Hub-and-Spoke%20Multi-Agent%20System/04-refinement-loop/)** — Add a bounded iterative refinement loop that re-investigates when the report agent flags a coverage gap.

### [Enforce Agent Compliance with Deterministic Hooks](Enforce%20Agent%20Compliance%20with%20Deterministic%20Hooks/)

A simulated banking transaction agent (`transaction_agent`) whose compliance guarantees live in
a hook engine — in code, not in the prompt. Built over three steps:

1. **[01-kyc-gate](Enforce%20Agent%20Compliance%20with%20Deterministic%20Hooks/01-kyc-gate/)** — A `PreToolUse` hook that blocks every money-movement tool until KYC has succeeded for that customer; the denied tool is proven to never execute.
2. **[02-normalization](Enforce%20Agent%20Compliance%20with%20Deterministic%20Hooks/02-normalization/)** — A `PostToolUse` hook that canonicalizes messy tool output (locale-aware currency → `Decimal`, epoch → ISO-8601 UTC, status codes → labels) before the model reads it.
3. **[03-interception-handoff](Enforce%20Agent%20Compliance%20with%20Deterministic%20Hooks/03-interception-handoff/)** — Intercept and redirect risky transfers to a compliance queue, produce a self-contained handoff summary, and run a harness proving deterministic enforcement beats even a maximal prompt.

## Working an Exercise

Each step's `starter/` and `solution/` is installed and tested the same way. From inside a step's
`starter/` or `solution/` directory:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

See the `README.md` inside each step for the exact TODO locations and the specific test file to run.
The projects use the Anthropic SDK for the live agent runners; the test suites are scoped so each
step can be verified on its own.

## License

See [LICENSE.md](LICENSE.md).
