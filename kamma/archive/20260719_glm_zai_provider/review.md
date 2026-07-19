# Review: GLM (Z.ai coding plan) provider

Date: 2026-07-19

## Reviews run
- **CodeRabbit CLI**: attempted twice (`--type uncommitted`, scoped `--dir`); first run timed out server-side, retry hit the free-tier rate limit. Not completed.
- **Independent adversarial subagent review**: completed, checked kwargs leakage, model-tuple unpacking, provider-name match, circular imports, tests.

## Findings
1. **`grounding` kwarg leaked into POST payload** (plausible severity): `AIManager.request()` always passes `grounding=...`; `ZaiManager.request` didn't consume it, so `"grounding": false` was injected into the JSON body via `payload.update(kwargs)`. Verified live that Z.ai tolerates the unknown field (200 OK), but hardened anyway to match the five siblings that declare `grounding: bool = False` explicitly. **Fixed.**

Clean on: model tuple timeout defaults, provider-name consistency, circular imports, test correctness.

## Verification after fix
- ruff check + format: clean
- pyright: 0 errors
- `uv run pytest tests/tools/`: 560 passed
- Live endpoint checks: `/models` lists glm-5.2 & glm-5-turbo; completions succeed with and without stray `grounding` field.

## Outcome
Accepted. User live-tested via gui2 pass2pre 2026-07-19 — confirmed working. Thread complete.
