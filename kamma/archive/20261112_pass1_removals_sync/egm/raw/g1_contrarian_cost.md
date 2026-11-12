Findings (file reads: 12; no code run).

## Problems

**1. Blocker — a valid removals file is "an allowed name" but silently never delivered.**
`scripts/server_contrib/contrib_pull.py:262-274` accepts a name only if `kind_of()` returns a kind; `kind_of` → `glob_parts` → `DELIVERED_KINDS`. `tools/contrib_entry.py:11-20` has no `pass1_auto_removed_*` entry. If step 1 is done by adding the kind to `DELIVERED_KINDS` only, deliver nothing until step 2 exists, the trap is worse: `kind_of` returns non-None, so `pass1_auto_removed_<user>.json` would fall through to `_check_lines` (`contrib_pull.py:130-131`), which does not validate JSON at all and returns `None` — accepted blindly, then `remove_users`/`copy_in` puts a `{book: [word]}` object into the laptop glob that the pull then parses as a list of lines.
*Fix:* register the kind in `DELIVERED_KINDS` and add it to `JSON_KINDS` (`contrib_pull.py:49`), plus a shape check that values are `list[str]`, else one bad file drops that contributor's day.

**2. Blocker — the pull's JSON validator rejects the real shape, and `_summarise` will crash on it.**
`_check_json` (`contrib_pull.py:147-151`) demands every value be a dict; the removed file is `{book: [word,...]}`. Route it to `_check_json` unchanged and the file is dropped for the contributor *and* all their additions. Worse, `_summarise` (`contrib_pull.py:443-447`) sums `len(json.loads(...))` for any name whose kind is in `JSON_KINDS` — it would report "N files, N entries" from the number of *books*, not words, for every contributor every day.
*Fix:* a separate `_check_removed` and exclude the kind from the entry-count loop, or the status line lies forever.

**3. Major — the write-back target is the tracked file, but the removal list cannot be pruned ("no pruning of the lists" in scope).**
`gui2/paths.py:110` plus `pass1_file_manager.py:74-84` make the list append-only and atomic; nothing ever removes a word from it. Combined with hypothesis (1) deleting from `gui2/data/pass1_auto_<book>.json`, the list keeps entries for words the tracked file no longer contains. Any later Pass1 Auto re-run on the laptop that re-adds the word (`pass1_auto_controller.py:127-134` `add_word`, no removal counterpart) is invisible on the server for that contributor forever. This is a permanent, unbounded correctness leak, not a disk one.
*Fix:* prune on the laptop after applying (`del removed[book][...]`), or key the list on `entry_hash`-style content so a stale word cannot revive as hidden.

**4. Major — YAGNI: a second source of truth where a repo already exists.**
The removed lists are per-user data in a folder whose every other file is delivered and reconciled (`contrib_reconcile.py:184-203`) against `additions_added.json`/`contrib_lines_merged.json`. Hypothesis (2) makes the server's *view* depend on every file in a shared folder (`add_contributor.sh:52`, `README.md:75`) — cross-user coupling never seen elsewhere in this design. Simpler: have the contributor's save already write the word into `additions_<user>.json` (it does — `save_router.py:60` `additions.add_additions`), and let the existing `reconcile_all` key match on `lemma_1`/`_source_key`. Then no new kind, no new check, no new pull step. The removed list only needs to exist because the server hides words from a *tracked* file it must not edit.
*Fix:* derive "hide" from existing delivered additions + a laptop-side `git`-tracked retirement (the `gui2/data/pass1_auto_retired/` folder already exists and is `.gitignore`d at line 107), instead of a new per-user channel.

**5. Major — Pass1 Add already has the answer: `is_missing`.**
`pass1_auto_controller.py:371-379` (`is_missing`) and `find_unknown_words` (`:405-431`) query the db/lookup per word. Pass1 Add calls `load_json` → `get_auto_processed_dict` (`:115-120`) which never consults the db (brief fact 5). The contributor's zero-latency fix is to filter the book dict by `db.all_inflections`/`lookup` at load time — no cross-user sync at all, and it also fixes the laptop-after-owner-adds case.
*Fix:* filter in `Pass1AddController.load_json`; keep the sync only for the "another user's word" case, if it is still wanted.

**6. Nit — cost.** New transfer is one 5 MB-capped file per contributor (`contrib_pull.py:42,45`), appended-only, so it grows monotonically and is re-listed and re-copied every run that is not skipped (max 30/day, `README.md:262`). Small today, unbounded in principle. Reading every contributor's list into `_read_view` on each `read()` (`pass1_file_manager.py:44-51`) is one JSON parse per keystroke-free click on a contributor box — fine, but the `read()` is inside the lock and re-reads from disk every call (`:53-55`). Fix: cache the merged dict, keyed on mtime.