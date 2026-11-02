# Results: no word finder for contributor servers (2026-11-02)

Commit under test: 267740fc (laptop and server the same, `server/results_wordfinder.md` `## 4.2`).
Builds on the previous thread: its after-values (943.3 MB warm, 1,045.7 MB after one book) are this thread's before-values.

## What was built

| Change | Laptop saving (MB) | Equivalence | Status |
|---|---|---|---|
| The word finder (manager + popup) is built only when the user has Pass2Add: gated in the warm-up, on Ctrl+F, on Ctrl+W and in the two shortcut rows (one condition, `7 in _visible`) | 170.0 (whole build, median of 3; range 170.0–170.1) | behaviour: new tests + live page check (below); no data changed | built, no role check; desktop unchanged |
| `Pass1AddController` drops its unused `wordfinder_manager` attribute and import (dead code, no reader) | included above | none needed (attribute removal) | built, every role |

## Laptop: whole build with and without the word finder

Source: `laptop.jsonl` (probe `lever_probe.py`, variants `contributor_real` vs `contributor_no_wordfinder`, three fresh processes each, 1.5 GB cap, read-only db copy, guard clean, swap 0).

| Variant | Final RSS median (min–max) |
|---|---|
| `contributor_real` (word finder built) | 909.1 (909.1–909.1) |
| `contributor_no_wordfinder` (this change) | 739.1 (739.0–739.1) |

**Saving: 170.0 MB per instance (range 170.0–170.1).** The variants differ in exactly one step (`wordfinder_today`); every other step is identical. The figure sits between the earlier thread's isolated estimate (172.1 MB) and its in-build estimate (159.8 MB), as a whole-build difference should.

## Server: before and after (one instance, `dpd-gui@alice`)

Source: `server/readings_wordfinder.jsonl`, labels ending `_wf`; table as written by the server agent in `server/results_wordfinder.md`. Before values from the earlier thread's `results.md` (`kamma/archive/20261102_contrib_mem_savings/artifacts/results.md`).

| Reading | Before (MB) | After (MB) | Change |
|---|---|---|---|
| 15 s after restart | 86.5 | 86.4 | 0 |
| Warm-up done | 943.3 | 774.1 | **-169.2** |
| After one book | 1,045.7 (peak 1,113.4) | 879.2 (peak 943.2) | **-166.5** (approximate, see caveat) |
| After Ctrl+F + shortcut list | n/a | 879.2 | the word finder was not built: the reading equals the one before it to the decimal |

Live checks on the page (no Pass2Add): Ctrl+F opened nothing; the shortcut list has no Ctrl+F row in the App group and no Ctrl+W row in the Popups group. All other rows unchanged.

Caveats:
- The one-book runs compare different work: the baseline ran `mn` (nothing to process, owner-confirmed) and this run ran `cp` stopped after about ten words (owner's instruction mid-run). The warm-up comparison (−169.2) is exact and sits right on the laptop's 170.0.
- The build logs no "App initialized" line, so the journal session-count check from the earlier thread is not possible; single-session evidence: one alice tab, no already-open banner, and readings far below the ~2 GB two-session figure of the earlier thread's invalid first run.
- The "Database loaded" and "All tabs and tools ready" snackbars fired before the page observer was installed (about 40 s gap); warm-up completion is evidenced by the journal's AI-manager init lines (03:48:54 server time) and the rendered tabs.
- The desktop is unchanged: with Pass2Add visible the warm-up, both keys and both rows behave as before (guard tests + live contributor page).

## Projection (baseline 1,066 MB plus N times per instance, same formula as before)

Per-instance figures after one book: before 1,045.7 MB, after 879.2 MB (peak: 1,113.4 vs 943.2).

| Contributors | Before (1,045.7 MB each) | After (879.2 MB each) | After, at peak (943.2 MB each) |
|---|---|---|---|
| 3 | 4,203 | 3,704 | 3,896 |
| 8 | 9,432 | 8,100 | 8,612 |
| 16 | 17,797 | 15,133 | 16,157 |

Eight contributors now fit a 16 GB server with about 7.9 GB to spare (was 6.5 GB). Sixteen fit in RSS with about 0.9 GB to spare but not at peak; the one-process rebuild (option E) is still the plan for more than 8.

## Done check (spec.md, "How we'll know it's done")

1. Met. Whole-build probe, median, min–max, three runs: `laptop.jsonl`, table above.
2. Met. Tests written first, failing reasons in `plan.md` 1.1; revert check per change in `plan.md` 1.4.
3. Met. `plan.md` 1.3 and 3.2: `tests/gui2` 630 pass; full suite 2,735 pass with the one listed pre-existing failure (`tests/tools/test_configger.py::test_profile_matches_original_script_writes[uposatha_reset]`); ruff clean on all four files; pyright on `gui2/main.py` equals HEAD's 24 pre-existing errors, test files 0; `just typecheck` 0 errors.
4. Met. `server/results_wordfinder.md` and `server/readings_wordfinder.jsonl` (copied to `artifacts/server/`), with 943.3 and 1,045.7 beside the new readings.
5. Met. Live page check in `plan.md` 4.3: Ctrl+F did nothing; shortcut list has no Ctrl+F or Ctrl+W row.
6. Met. `plan.md` 3.1 and 3.2: CodeRabbit 0 findings; DeepSeek 2 findings, the real one (misleading comment) fixed, the other no-action by design.

## What is left

- Option E (one process for all users) when there are more than 8 contributors.
- The "refresh DB" extra memory and the detector rebuild worker: untouched, as spec.md excludes.
- `gui2/wordfinder_widget.py` remains dead code, untouched per spec.
