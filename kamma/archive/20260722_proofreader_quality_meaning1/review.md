## Thread
- **ID:** 20260722_proofreader_quality_meaning1
- **Objective:** Tighten the AI proofreader (`just proofread`) so a full-database pass over `meaning_1` produces a short, usable queue of obvious spelling/grammar fixes, add an incremental re-check cache so repeat runs only re-check edited ids, and fix a concurrent-writer race with gui2's PRead.

## Files Changed
- `tools/proofreader.py` — prompt rewrite, zai→deepseek model fallback, incremental cache (`proofreader_checked.json`), TSV queue merge, cross-process file locking (`filelock`), atomic writes
- `tools/paths.py` — added `proofreader_checked_json_path`
- `tests/tools/proofreader/test_proofreader_ai.py` — updated for new `process_batch` signature, `-> None` annotations added
- `tests/tools/proofreader/test_proofreader_cache.py` — new: cache, TSV merge, locking, and normalization tests
- `justfile` — added `proofread` recipe (MAINTENANCE)
- `.gitignore` — ignore generated TSV/cache/lock/tmp files
- `pyproject.toml` / `uv.lock` — added `filelock` dependency
- `tools/proofreader.tsv` — untracked (`git rm --cached`, staged not committed)

## Findings

Reviewed independently by a fresh subagent (sections 4.0–6.0) and `coderabbit review --agent --uncommitted --include-untracked --base main` in parallel.

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `tools/proofreader.py` `save_checked_cache`/`save_tsv_queue` | In-place `open(...,"w")`/`write_text` writes, not atomic | A kill mid-write truncates the file; cache load then discards the whole cache (forcing a full 63k re-check) or the TSV silently drops pending PRead corrections | Write to `.tmp` sibling + `Path.replace()` |
| 2 | major | `tests/tools/proofreader/test_proofreader_cache.py` (old `test_merge_preserves_...`) | Test re-implemented the merge loop inline instead of calling `main()`'s real logic | Zero safety net if the real merge logic breaks later | Extracted `apply_checked_item()` and `build_corrected_by_id()` from `main()`; tests now call the real functions |
| 3 | minor | `kamma/.../spec.md` acceptance checklist | All 6 boxes left unchecked despite being verified | Misleading thread status | Ticked all 6 with verification notes |
| 4 | minor | `plan.md`/`spec.md` model-order wording | "empty/invalid JSON" was ambiguous — could misread as "empty corrections list `[]`" (a success) as a failure trigger | Could mislead a future reader about fallback semantics | Reworded in both files: fallback triggers only on no-content/unparseable JSON; `[]` is an explicit success |
| 5 | minor | `git rm --cached tools/proofreader.tsv` | File had been re-tracked (an unrelated automated "data update" commit in this repo re-added it to the index after the original `git rm --cached`) | Contradicted spec/plan's stated intent; would keep diffing as a tracked file | Re-ran `git rm --cached`, confirmed staged deletion + gitignored |
| 6 | minor | `tools/proofreader.tsv.lock` not gitignored | `filelock` leaves a lock file next to the TSV | Would show as a stray untracked file after every run | Added `.lock` and `.tmp` patterns to `.gitignore` |
| 7 | minor | `justfile:215` comment | Said "rebuild" — stale since Phase 3 replaced wipe-on-write with a merge | Misleads about whether it's safe to interrupt/rerun | Reworded to "incrementally updating" |
| 8 | nit | `tests/tools/proofreader/test_proofreader_ai.py` | Test functions missing `-> None` | Project convention: type hints everywhere, especially on touched files | Added to all test functions in both proofreader test files |
| 9 | nit | `save_checked_cache` full-file rewrite every batch (~2,500× over a full run) | O(n) per batch, compounds but cheap at this file size | Not worth optimizing now | No action — noted only |
| 10 | nit | `AIManager` collapses "no provider configured" and "API call failed" into the same generic error | Pre-existing behavior, not introduced by this thread | — | No action — out of scope |

## Fixes Applied
- Atomic writes (temp file + `os.replace`) for both `save_checked_cache` and `save_tsv_queue`.
- Extracted `apply_checked_item()` and `build_corrected_by_id()` out of `main()`; both now directly unit tested (previously only simulated).
- Re-ran `git rm --cached tools/proofreader.tsv` (had silently reverted via an unrelated repo automation commit).
- Added `tools/proofreader.tsv.lock`, `tools/proofreader.tsv.tmp`, `tools/proofreader_checked.json.tmp` to `.gitignore`.
- Reworded ambiguous "empty/invalid JSON" language in `spec.md` and `plan.md`.
- Ticked all 6 acceptance-criteria checkboxes in `spec.md` with verification notes.
- Fixed stale `justfile` comment.
- Added `-> None` return annotations to all test functions in `test_proofreader_ai.py` and `test_proofreader_cache.py`.

## Test Evidence
- `uv run pytest tests/tools/proofreader/ -q` → **23 passed**
- `uv run ruff check --fix` (all touched files) → all checks passed
- `uv run ruff format` (all touched files) → clean
- `uv run pyright` (all touched files) → 0 errors, 0 warnings
- Threaded lock tests use `threading.Event`/`.wait(timeout=...)` for deterministic synchronization, not flaky sleeps.
- Real production run confirmed working: GLM quota checked mid-run (9% of 5h window), restarted cleanly twice, cache correctly resumed each time; user spot-checked ~100 real rows via PRead and was satisfied with signal quality.

## Verdict
PASSED
- Review date: 2026-07-22
- Reviewer: independent subagent + coderabbit review --agent (parallel), findings consolidated and fixed in this session
