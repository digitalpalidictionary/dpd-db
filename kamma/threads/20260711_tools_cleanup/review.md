# Review: tools/ folder cleanup (#157)

## Verdict: PASS

Two independent sonnet subagent reviews run in parallel, plus manual verification.

## 1. Kamma review-phase (spec/plan vs. diff audit) — PASS WITH NOTES
- Diff scope: every changed file accounted for by spec.md/plan.md. Files outside
  scope (`.gitmodules`, `db_tests/`, `shared_data/`, `resources/tpr_downloads`,
  `tools/phonetic_changes.tsv`, one hunk in `tools/phonetic_change_manager.py`)
  confirmed to belong to the separate parallel `20260711_db_tests_triage` thread —
  excluded from this thread's commit.
- Dead-code removal: spot-checked all 20 removed functions with fresh `rg --hidden`
  sweeps + `git show HEAD:<file>` — all confirmed zero live callers pre-removal.
- No-output-change constraint: read every diff in tools/gui2/exporter/analysis/
  scripts — all mechanical (docstrings, type hint modernization, import
  relocation) except the two documented bug fixes. One minor undocumented note:
  `missing_meanings.py::check_in_dpd_headwords` gained a `headword is None`
  guard (defensive null-check, not a behavior-affecting fix in practice).
- Test quality: spot-read 7 of 28 new/relocated test files — genuine
  behavior-locking tests, tmp_path isolated, real edge cases, no tautologies.
- Full suite: 1722 passed, 16 deselected — matches baseline exactly.
- Lint gate: ruff check/format + pyright clean across all 82 touched files.

## 2. CodeRabbit review (`coderabbit review --agent --base main --type uncommitted`) — 8 findings
| Finding | File | Verdict | Action |
|---|---|---|---|
| untyped `all` param | tools/niggahitas.py | valid | fixed: `all: bool = True` |
| use tools.printer not rich.print | scripts/fix/gatha_cleaner.py | invalid | rich.print is the established convention across scripts/fix, scripts/find |
| main() missing -> None | scripts/fix/gatha_cleaner.py | valid | fixed |
| docstring typos | scripts/fix/gatha_cleaner.py | valid | fixed |
| clean_gatha missing type hints | scripts/fix/gatha_cleaner.py | valid | fixed |
| sanskrit_translit test should match "standard" HK mapping | tests/tools/test_sanskrit_translit.py | invalid for this pass | production `hk_translit`/`slp1_translit` S/z mapping looks genuinely swapped vs standard HK/SLP1 (confirmed: produces kṛśṇa not kṛṣṇa), but fixing only the test would desync it from real, currently-shipping exporter output — a production behavior change outside this cleanup's scope. Flagged for a separate deliberate fix. |
| missing_meanings level checks not cumulative | scripts/find/missing_meanings.py | valid, real bug | fixed: `==` -> `>=` for level 2/3 checks (docstring already promised cumulative levels) |
| missing_meanings missing type hints | scripts/find/missing_meanings.py | valid | fixed |

All fixes verified: `ruff check`/`ruff format`/`pyright` clean on the 3 touched
files; full suite 1722 passed, 16 deselected (unchanged).

## Bugs found across this thread (cumulative)
1. **Fixed**: `missing_meanings.py` ignored its `level` parameter (hardcoded 1).
2. **Fixed** (user instruction): `clean_sentence.py` mutated the shared global
   `pali_alphabet` list instead of a local copy.
3. **Fixed** (CodeRabbit): `missing_meanings.py` level checks used `==` instead
   of `>=`, so level 3 didn't also apply level 2's check as the docstring promised.
4. **WONTFIX** (user decision): `uposatha_day.py` uncaught `NoSectionError` —
   accepted risk, locked by test.
5. **Flagged, not fixed** (out of scope, needs its own deliberate PR):
   `tools/sanskrit_translit.py` HK/SLP1 `S`/`z` mapping appears swapped vs.
   standard convention. Predates this thread, feeds live mobile exporter output
   and the `resources/other-dictionaries` submodule (same swap there). Not
   touched — production output change requiring explicit sign-off.

## Final status
Full suite: 1722 passed, 16 deselected. Lint/pyright clean on every file this
thread touched. Ready to finalize.
