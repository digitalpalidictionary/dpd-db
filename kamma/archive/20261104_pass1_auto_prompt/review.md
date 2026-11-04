## Thread
- **ID:** 20261104_pass1_auto_prompt
- **Objective:** Build a better Pass1 Auto prompt and context, prove it beats the old one, then ship it in gui2.

## Files Changed
- `gui2/pass1_context.py` (new) — sentence picker, related entries, allowed values, old and new prompt builders.
- `tools/epitaka_sentences.py` (new), `tools/paths.py` — read-only ePitaka sentence reader and PEU lookup, plus their paths.
- `gui2/pass1_auto_controller.py` — uses the new builder, picks up to 3 sentences, new system prompt, `remove_word` goes through `Pass1FileManager.remove`.
- `gui2/pass1_file_manager.py`, `gui2/paths.py` — per-user removals list for contributors; tracked files are never written on the server.
- `gui2/books.py` — books vv, pv, ap, bv.
- `gui2/contributor_tabs.py`, `gui2/main.py` — Pass1Auto hidden for contributors; server start tab is Pass1Add.
- `.gitignore` — live `pass1_auto_*.json` tracked; removals list, text scratch file and the retired-backup folder ignored.
- `kamma/tech.md`, tests under `tests/gui2/` and `tests/tools/`.

## Findings
Sources: DeepSeek flash (`deepseek-flash`, DeepSeek API, reasoning off, 6 pieces), CodeRabbit (tools: 2 findings; tests: 0; gui2: failed twice, see Not Verified), own read. Every finding was checked against the code.

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `gui2/pass1_file_manager.py` | A removals file holding valid non-object JSON (`[]`) broke `read()` | One stray edit hides the whole book from a contributor | Fixed: non-dict is treated as empty |
| 2 | minor | `gui2/pass1_file_manager.py` | Removals list written in place | A crash mid-write empties it and every removed word reappears | Fixed: write temp file, then replace |
| 3 | minor | `tools/epitaka_sentences.py` | Absent PEU file was cached as empty (CodeRabbit) | A file installed later in the session was never seen | Fixed: check the file before the cached loader |

Rejected after checking (no change): deadlock in `remove` (the update call runs outside the lock; the primary-user test would hang); `add_word` and temp-file writes on the server (the server has no Pass1 Auto run); stale allowed values, per-word new session, related-entry lookup (same as the old code); unused imports (ruff passes); lower-casing the PEU lookup word (callers pass cleaned lower-case words); catching a corrupt ePitaka file (an empty result would hide a real fault).

## Fixes Applied
- Findings 1–3 above, with new tests. Reverting finding 3's fix makes `test_peu_file_installed_later_is_found` fail (1 failed); restored, 10 pass.
- Owner decision during review: retired backups stay local. `.gitignore` ignores `gui2/data/pass1_auto_retired/`; spec and plan updated.

## Test Evidence
- `uv run pytest tests` (scope: whole repo) → 2928 passed, 1 failed, 12 deselected. The failure is `test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason`.
- `uv run pytest tests/scripts` (scope: that folder) → 357 passed, so the failure appears only in the full run. Not touched by this thread; not checked against a clean tree.
- `uv run pytest tests/gui2 tests/tools/test_epitaka_sentences.py` (scope: this thread's tests) → 688 passed.
- `just typecheck` (scope: whole repo, re-run after the review fixes) → 0 errors.
- `uv run ruff check`, `ruff format`, `pyright` (scope: every touched file; gui2 and tests with `--project /dev/null`) → clean, except `gui2/main.py`, which has 24 old pyright errors on untouched lines.

## Not Verified
- CodeRabbit on `gui2/` failed twice with a connection drop; no CodeRabbit result for gui2. The first whole-tree run was refused (274 files, limit 150), so `kamma/` was never sent.
- DeepSeek flash timed out at reasoning levels "max", "high" and "medium" (4 runs). It answered at "off" on 6 small pieces. The test files were not sent to it, and its depth is lower than at higher reasoning.
- The AI answer quality in the GUI beyond the owner's run on several `vv` words.

## Verdict
PASSED
- Review date: 2026-11-04
- Reviewer: Claude (Sonnet 5.5) with DeepSeek flash and CodeRabbit
