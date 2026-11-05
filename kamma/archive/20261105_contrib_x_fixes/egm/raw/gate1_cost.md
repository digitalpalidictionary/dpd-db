Enough. Writing findings.

## Findings

**Blocker — #8 deletes the rollback copy, so a later failure has no way back (data loss risk on the live server).**
`scripts/server_contrib/maintenance_window.py:284-289` copies the whole db to `dpd.db.prev` on every run past the dirty check; `:330-346` restores from it. The brief's "delete after a good run only" is safe *only* inside the `try` after `outcome == REBUILT` and *outside* the rollback's reach; placed anywhere near `last_built.write_text` (`:429`) the same `except` at `:432` fires on a later `_apply_wal`/`_restore_build_changes` failure and now finds no backup. Failure scenario: rebuild passes, cleanup runs, `_restore_build_changes` (`:396-411`) fails → `_restore_rollback` runs with `dpd.db.prev` gone → live db is the half-finished build, no restore. Fix: delete only in the `finally` guarded by `outcome is Outcome.REBUILT`, and never in the `try`. Contrarian's Blocker agrees; treat the brief's `:35` "not read in code" line as disqualifying for this item.

**Blocker — #8's `_contrib_worktree/` target is owned by another module and is not a leftover.**
`scripts/server_contrib/contrib_push.py:51-56` creates it and `:67` reuses it across runs; deleting it after a good run forces a full `git worktree add --detach` (whole tree checkout) the *next* night, adding minutes of I/O and `git fetch` on a 2 GB-scale repo, and `:52-56` shows a hand-deleted folder is a known hazard (`prune` needed). Failure scenario: cleanup succeeds, next window re-clones the worktree while instances are stopped, extending downtime. Fix: drop the worktree deletion from #8 entirely; `git worktree add` is idempotent and the folder is a cache, not waste.

**Major — #7's "notice on every skip" multiplies notifications and fights the existing design.**
`contrib_pull.py:596` deliberately filters skips; `maybe_notify` (`:559-572`) announces only problems. Removing the filter fires a desktop notice for `skipped: another run` (`:519`), `skipped: already done today` (`:522`) and every editor-open skip (`:476`, `:526`). Failure scenario: a cron every few minutes with the editor open all day → one `notify-send` per run, process spawn + 10 s timeout each (`:555-560`), a notification storm that trains the maintainer to ignore it. Fix: notify at most once per day per skip reason (or keep the filter, as today).

**Major — #5 adds a full 800k-row corpus reload; on the server that reload is the expensive path.**
`database_manager.py:795-804` renames *all* headwords with a pattern (bulk `update`), so `mark_corpus_stale()` (`:261-265`) invalidates the cache used by `make_inflections_lists` (`:412`), `make_pass2_lists` (`:496`), `make_components_lists` (`:523`) and `RelationshipDetector` (`:885`). Each reloads `load_corpus()` and, on the contributor server, re-runs `_load_contributor_corpus()` (`:236-258`) — two full scans plus ~80k rows materialised twice, then sorted. Failure scenario: a contributor editing templates renames a pattern used by many words, then opens Pass2 → several serial multi-hundred-MB reloads and visible stalls. Fix: mark stale (correct for consistency) but coalesce — invalidate lazily and let the existing `_corpus_gen` guards skip rebuilds; do not add an eager reload.

**Major — #3's read-only probe adds a query/connection per cache refresh.**
`database_manager.py:388-396` already catches the failure and prints. "Skip quietly when read-only" needs a new probe (PRAGMA or `os.access`) executed on every decon cache refresh; at line 391 `save_decon_no_headwords_cache` already runs on every startup/refresh. Failure scenario: probe says writable, write still fails on a locked db taken by the nightly build (`:393` comment) → same print path, now plus one wasted probe per refresh. Fix: delete the `print`, keep the `except`; zero new queries.

**Nit — #4/#12 touch the contributor server's peak load only by accident.**
`start_dpd_server` spawns uvicorn on `127.1.1.1:8080` (per contrarian, `tools/fast_api_utils.py:21-35`), yet `justfile:156-157` already runs `webapp`. Removing it *slightly* lowers desktop RSS; #12 (`page.web`) adds one attribute read. Neither changes server load. Note the brief's own unverified assumption (`brief.md:39`) — if `page.web` is wrong, Alt keys silently vanish on desktop, not a cost issue.

**Nit — #11's column preset changes DB-tab query shape, not size.**
Showing `id, pos, grammar, meaning_1, meaning_2, meaning_lit` is narrower than today's row set, so it *cuts* bytes pulled; but confirm the tab still `load_only`s those columns or Flet will still fetch full rows including `inflections_html` (7.5 KB/row per `:236-241`). Failure scenario: preset narrows the UI only and the query stays full-width — no savings. Fix: ensure the preset feeds `load_only`.

**Breakage at scale, summary:** the rollback copy (`:284-286`) already duplicates the db nightly with no size check; #8 as written either keeps that copy forever (no saving) or removes it at the wrong moment (data loss). The real peak-load lever in this thread is #5's forced corpus reload, not the cleanup.
