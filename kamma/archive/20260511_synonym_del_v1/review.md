## Thread
- **ID:** 20260511_synonym_del_v1
- **Objective:** Rewrite `add_synonym_variant_del.py` to flag and review
  synonym pairs that don't meet validity, with logic refined to avoid
  noise from homonyms and cross-pos targets.

## Files Changed
- `db_tests/single/add_synonym_variant_del.py` — full rewrite. Soft
  gating (≥1 shared cleaned meaning), same-pos restriction,
  dangling-reference flagging, own exceptions file, prompt
  s/t/d/e/pass/r/q, search string copied to clipboard via pyperclip.
- `db_tests/single/add_synonym_variant_multi.py` — `_entry_label` now
  prints `hw.meaning_combo` instead of `hw.meaning_1` (also affects
  `_single` and `_del`, which import it).
- `tools/paths.py` — added `syn_var_del_exceptions_path` pointing at
  `db_tests/single/add_synonym_variant_del.json`.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `add_synonym_variant_del.py:71` | `_is_valid_synonym` is unused at runtime | Kept intentionally as a documented revert path for the soft-gating change | Leave as-is; documented in plan.md |

## Fixes Applied
- Updated stale module docstring to describe the actual soft-gating
  behaviour (was still describing the original strict ≥2-shared rule).

## Test Evidence
- `uv run ruff check db_tests/single/add_synonym_variant_del.py db_tests/single/add_synonym_variant_multi.py tools/paths.py` → pass
- `uv run python -m py_compile <same three files>` → pass
- User exercised the script live against the real DB across several
  iterations: `akatavedī`/`akataññū` (homonym false-positive fixed),
  `akkhema`/`bhaya 2` (cross-pos false-positive fixed),
  `ativiya`/`bhusaṃ 2` (soft-gating false-positive fixed),
  `alagga` (meaning_combo now visible), `s` and `t` choices added.

## Verdict
PASSED
- Review date: 2026-05-11
- Reviewer: kamma (inline)
