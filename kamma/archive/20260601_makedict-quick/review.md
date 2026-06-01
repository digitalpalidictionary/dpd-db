## Thread
- **ID:** 20260601_makedict-quick
- **Objective:** Add a fast `makedict-quick` build that turns off every off-able step (config.ini driven), producing the DPD GoldenDict/MDict only.

## Files Changed
- `tools/configger.py` — added `[generate]` block to `DEFAULT_CONFIG` (suttas, grammar, inflections_to_headwords, epd, search_index = yes)
- `config.ini` — added `[generate]` section (gitignored; not committed)
- `db/suttas/suttas_update.py` — guard on `generate.suttas`
- `db/suttas/suttas_to_lookup.py` — guard on `generate.suttas`
- `db/grammar/grammar_to_lookup.py` — guard on `generate.grammar`
- `db/inflections/inflections_to_headwords.py` — guard on `generate.inflections_to_headwords`
- `db/epd/epd_to_lookup.py` — module-level guard on `generate.epd` (work runs in class body at import, so a main() guard is too late)
- `exporter/webapp/generate_search_index.py` — guard on `generate.search_index`
- `scripts/build/config_quick_profile.py` — NEW; `apply_quick_profile()` + `reset_generate_components()` (dispatch via `reset` arg)
- `scripts/build/config_uposatha_day.py` — release path also re-enables the five `[generate]` gates
- `justfile` — NEW `makedict-quick` recipe: apply quick profile → makedict → reset generate gates

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `justfile` | "off-able" is a coinage, not OED English | cosmetic | User chose to keep it deliberately |

No blocking or major findings.

## Fixes Applied
- Added post-build `reset` step so the `[generate]` gates never linger off (user request).
- Wired `[generate]` resets into `config_uposatha_day.py` so release builds stay complete.

## Test Evidence
- `uv run ruff check <all changed .py>` → pass
- `uv run pytest tests/exporter/webapp/test_generate_search_index.py` → 3 passed
- `just --list` → `makedict-quick` registers

## Known tradeoffs (documented, accepted)
- `makedict-quick` skips lookup-rebuild steps; lookup table keeps prior data until a full build.
- The post-build reset re-enables only the `[generate]` gates. Exporter flags (make_grammar/make_deconstructor/make_tpr/make_audio_db) and anki.update stay off until restored manually or via the uposatha release path.

## Verdict
PASSED
- Review date: 2026-06-01
- Reviewer: kamma (inline)
