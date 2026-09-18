## Thread
- **ID:** 20260917_flet_1_0_migration
- **Objective:** Migrate `gui2/` and the `db_tests/gui/` helpers from Flet 0.28.3 to 1.0.0, preserving behaviour.

## Files Changed
- `gui2/dpd_fields_classes.py` — BR-27 `error_text`→`error` forwarding property; `before_update()` derives the error border; BR-28 `expand=True` on `DpdDropdown`
- `gui2/ui_utils.py` — new `set_error()` for bare `TextField`s (review fix)
- `gui2/user.py`, `gui2/ai_search_window.py`, `gui2/dpd_fields_commentary.py`, `gui2/dpd_fields_examples.py` — routed through `set_error`; dead border writes removed
- `gui2/pass1_add_view.py`, `gui2/pass2_add_view.py` — `.error_text` → `.error` on bare fields
- `db_tests/gui/main.py` — BR-29 `page.run_thread` dispatch, teardown in `finally`
- `db/backup_tsv/backup_dpd_headwords_and_roots.py` — path-limited commit (review fix)
- `artifacts/check_error_text.py`, `check_phase6.py`, `diff_wiring.py`, `wiring_diff.md`, `handover.md` — new guards and Phase 7 evidence
- ~40 further `gui2/` files from Phases 3–5 (renames, async conversions, borders)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `db/backup_tsv/backup_dpd_headwords_and_roots.py:164` | `index.add()` + `index.commit()` commits the **whole index**, not just the backup TSVs | This tree is shared by parallel sessions; a backup would sweep their staged work into a "pali update" commit. The thread had already touched this function for the same class of bug | Path-limited `repo.git.commit("-m", …, "--", *files)`. Semantics proved in a throwaway repo: only the named file committed, other staged work left staged |
| 2 | major | `gui2/dpd_fields_classes.py:96` (BR-28) | `expand=True` re-added is a direct reversal of BR-25's removal; the retest cannot distinguish a correct result from a re-broken one | Pass1Add has a different row shape, so its dropdowns are now far wider than their 0.28 baseline while still "aligned" | **Not fixed — needs one look.** Documented in spec BR-28 and raised as the handover's first open check |
| 3 | minor | `gui2/user.py`, `ai_search_window.py`, `dpd_fields_commentary.py`, `dpd_fields_examples.py` | 4 bare `TextField`s got the error message back but not the red border — they carry an explicit `border=`, which overrides 1.0's theme-resolved error border | Undocumented visual regression on 4 fields outside the area the user was asked to test | Added `ui_utils.set_error()`; 6 sites use it. 2 clear-only sites left alone (one has its own blue resting border) |
| 4 | minor | `artifacts/check_error_text.py` | Guard missed local variables, `AnnAssign`, `AugAssign`, and bare-import constructors; "sensitivity proved" overstated its coverage | It is the regression guard for the thread's largest fix and is cited as evidence | Extended to all four shapes; re-tested against 6 bad fixtures (all caught) and 3 correct spellings (all silent) |
| 5 | minor | `gui2/dpd_fields_examples.py:582,586` | Hand-set borders now dead — `before_update()` recomputes the identical value | Misleads the next reader into thinking they matter | Removed, with a comment saying why |
| 6 | minor | plan / handover / improvements | Stale counts: 17→**21** non-`gui2` files, "eight"→**12** guard scripts, 48→**50** field definitions, 115→**117** `field_border` calls, "six raw sites"→**8 sites across 6 files** | The thread's credibility rests on measured numbers; `check_error_text.py` was absent from every guard list | All re-measured and corrected |
| 7 | minor | `spec.md` BR-29 | Cross-thread `page.update()` claimed to work with no caveat | 1.0's patch generation has no lock; the one end-to-end run never exercised contention | Caveat recorded in BR-29 and the handover watch list |

Reviewers also flagged the two `db/` files as foreign to this thread — **wrong**: `git log` shows both committed in the Phase 5 commit. Finding 1 follows from that.

## Fixes Applied
- Findings 1, 3, 4, 5, 6, 7 fixed. Finding 2 documented and escalated — it needs a human look at one screen.
- CodeRabbit findings not actioned, with reasons: obsolete higher-numbered `*_part_*.tsv` files not pruned after a split (pre-existing, out of scope per spec); re-entrancy in `ai_search_window` / `tests_tab_controller` / `translations_view` (0.28 ran sync handlers on worker threads, so concurrent starts were already possible — not introduced here); `_click_add_to_db` blocking the loop (already recorded as a known Phase 4 carry-forward); 7 further guard-blind-spot findings on earlier-phase guards (same class as finding 4, no live miss — left rather than widened mid-review).

## Test Evidence
- `uv run pytest tests/` (scope: whole project, 245 test files) → 1886 passed, 12 deselected
- `uv run pytest tests/gui2/` (scope: editor tests) → 284 passed
- `just typecheck` (scope: repo-wide pyrefly, ~390 files) → 0 errors
- `uv run ruff check` / `ruff format --check` (scope: all 57 touched `.py`) → clean
- `uv run pyright` (scope: 57 touched files, but **21 real** — `gui2` is excluded from both checkers, `filesAnalyzed: 0`) → 0 errors
- `capture_wiring.py` → `diff_wiring.py` (scope: all 448 live handler bindings vs the 449 in-scope baseline) → zero unexplained differences
- 10 `check_*.py` guards → all exit 0; `check_error_text` re-proved against 6 bad and 3 good fixtures
- Path-limited commit semantics → proved in a throwaway git repo, not asserted

## Not Verified
- **BR-28 on Pass1Add** — finding 2. Pixels cannot be measured statically and the GUI was not run.
- Three of BR-16's four border signals; BR-22's focused ring; catalogue §1.3's per-field dropdown behaviours.
- Cross-thread `page.update()` safety under contention (finding 7) — reasoned from the wheel, never stressed.
- `gui2/` has no type checking from either checker — ~36 rewritten files rest on tests and review alone.
- The behaviour catalogue was not walked binding-by-binding; the user's 15-check round plus 4 retests stands in for it.
- 7 earlier-phase guards were run but not adversarially tested by me.

## Verdict
PASSED — with one open visual check
- Findings 1 and 3–7 are fixed and re-verified. Finding 2 changes no code and blocks nothing mechanical, but the user should look at Pass1Add's dropdowns before this is considered closed; if the width is wrong there, it is a one-line change to per-row-shape handling.
- Review date: 2026-09-18
- Reviewers: independent Sonnet subagent (whole thread), CodeRabbit CLI (`--base main --include-untracked`, 16 findings), and two independent external reviewers on Phases 6–7.
