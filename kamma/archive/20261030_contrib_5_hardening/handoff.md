# Handoff — contrib_5 hardening (updated 2026-10-30, after Phase 6)

## State
Phases 1-6 are done and marked `[x]` in `plan.md`. Nothing is committed.
Phase 7 DONE and review PASSED (`review.md`, 2026-10-30). Next: `/kamma:4-finalize`.

## Gates run
- Phase 5: ruff + format clean, pyright 0 errors, `just typecheck` 0 errors.
  `uv run pytest tests/scripts/server_contrib tests/gui2 tests/tools tests/db
  tests/db_tests -m "slow or not slow"` = 1803 passed.
- Phase 6: `bash -n` OK; hand run of `add_contributor.sh --root` OK.

## What Phase 5 changed (read plan 5.x DONE notes and spec G.a-G.g)
- `tools/contrib_entry.py` now holds `DELIVERED_KINDS` and `delivered_files`.
- `merge_contrib_files.py` keeps `gui2/data/contrib_lines_merged.json`.
- `just contrib-merge` = fetch `origin/contributions`, merge, run the merge script.
- Backup & Quit commits the two `*_added.json` logs and the merged-lines log.
- Reconcile, push (worktree) and the window were rewritten; the absorption
  check and its test are deleted. README rewritten.

## Open items
- Flet under the `/<user>/` nginx path is unverified (plan 6.1). Prove it in
  contrib_4 Phase 4; fallback is one sub-domain per user.
- 3.4: a correction with `_changed` shows only changed fields (see plan note D).
- Spec C.7 (reload of the live tab) is only checkable live, task 7.1.
- Unrelated dirty file: `shared_data/deconstructor/variant_readings.tsv`.
- `just contrib-merge` stops on a conflict; the README says to abort the merge
  and wait for the next night's branch.
