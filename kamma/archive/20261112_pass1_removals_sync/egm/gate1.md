# Gate 1 — idea stress test

Backend: pi, DeepSeek API (`--provider deepseek --model deepseek-flash --thinking off`, tools read/grep/find/ls), streamed as JSON events (kept outside the repo; final answers in `raw/*.md`).
Smoke probe: passed (read tool used, first line of `brief.md` returned in seconds; answer in `raw/probe.md`).
Reviewers: 3, lenses paired (small thread): contrarian + cost (no facts list), UX + observability, migration + maintenance. All exited 0. No backend switch.

## Disposition

| # | Finding (deduplicated) | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| F1 | `_check_json` demands dict values; a `{book: [word]}` list fails, and `remove_users` then drops ALL that contributor's files | Blocker | Accept | read `contrib_pull.py:134-152`, `:299-304` | spec: own validator for the new kind |
| F2 | `_summarise` counts top-level keys of JSON kinds as "entries"; books would be counted as entries | Nit | Accept | read `contrib_pull.py:434-450` | spec: kind stays out of `JSON_KINDS`; words counted separately |
| F3 | `DELIVERED_KINDS` is also the push's copy list (`git add -f`), so a gitignored list would ride the `contributions` branch | Major | Accept | read `contrib_push.py:76-83` | spec: a pull-only allowlist entry, not `DELIVERED_KINDS` |
| F4 | Book keys from a contributor file used to build `pass1_auto_{book}.json` path = path traversal on the laptop | Blocker | Accept | read `pass1_file_manager.py:24-25` | spec: keys only ever used as dict lookups / matched against existing file names |
| F5 | A word deleted on the laptop but not yet in `dpd.db` is re-found by `is_missing` and re-added on the next Pass1 Auto run | Major | Accept (the claim that Pass1 Auto rewrites the whole file is false: `add_word` per word, `pass1_auto_controller.py:127-134`, `:583`) | read `is_missing` `:371-381` | spec: `is_missing` also skips words in any removed list |
| F6 | Removed lists are never pruned and grow forever | Nit | Reject pruning | pruning re-opens F5; growth is a few words a day under the pull's 5 MB cap (`contrib_pull.py:42`) | spec: "not included" |
| F7 | The pull editing tracked book files: contributor input deletes words from the owner's queue; dirty tree blocks the nightly ff-only pull | Major | Escalate (architecture fork) — dirty-tree part rejected: the laptop already dirties these files through its own Pass1 Add/Auto (8 "data update" commits 2026-11-04..11), and the nightly `git pull --ff-only` runs on the server's tree, not the laptop's | `git log -- gui2/data/pass1_auto_*.json`; `maintenance_window.py:9` | owner decided 2026-11-12: option A (delete from laptop book files, so the deletion shows in his git diff) — spec items 4–6 |
| F8 | No trace of which removals arrived or were applied | Major | Accept | read `contrib_pull.py:428-450` | spec: per-contributor count in the status line, one log line per run |
| F9 | A contributor's open snapshot keeps offering words another contributor finished meanwhile | Major | Reject | one book per contributor is the operating rule (`pass1_file_manager.py:12-16`); the view is re-read on book load; a duplicate reaches the owner as two additions he reviews | — |
| F10 | Pass1 Add says "deleted" on the server, where nothing is deleted | Nit | Reject | not asked; wording only | — |
| F11 | YAGNI: derive hiding from the contributor's additions instead of a new channel | Major | Reject | additions hold headword columns only (`pass1_add_controller.py:151-155`), no `word_in_text`; `lemma_1` is not the inflected text word | — |
| F12 | Filter Pass1 Add by the db's inflections at load time instead | Major | Reject as the fix | a contributor's word is in no db until the owner processes the addition and the server rebuilds (`save_router.py:38-60`), so it misses the asked case; noted in spec as not included | spec: "not included" |
| F13 | `read()` re-reads list files on every call | Nit | Reject | `get_auto_processed_dict` caches per book (`pass1_auto_controller.py:115-120`); lists are a few KB | — |
| F14 | No rollback for a laptop-side deletion | Nit | Reject | git holds the tracked file; moot if the fork picks hiding | — |

Totals: 14 deduplicated findings — accepted 6 (F1–F5, F8), rejected 7 (F6, F9–F14), escalated 1 (F7).

## Raw findings

### g1_contrarian_cost

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


### g1_ux_observability

I have what I need.

# Findings

## 1. Blocker — `_check_json` rejects the removals kind, so a pull kills the contributor's real work
Next to `tools/contrib_entry.py:13` (JSON kinds are `additions`, `corrections`) and `scripts/server_contrib/contrib_pull.py:139-147`: `_check_json` demands every value be a dict. A removals file is `{book: [word, ...]}`. The moment `pass1_auto_removed_*.json` is added to `DELIVERED_KINDS`, the pull reports "a JSON entry is not an object" for that user, and `remove_users` (`contrib_pull.py:290`) drops **all** their files — their additions included. A contributor's whole day vanishes, and the status line reads `alice: skipped, pass1_auto_removed_alice.json: a JSON entry is not an object`. Fix: give the new kind its own validator (`dict[str, list[str]]`, book names taken from `sutta_central_books` + "text", each word a `str`), and never let one bad kind drop sibling kinds.

## 2. Blocker — the deletion is applied to the laptop's tracked file behind the owner's back, with no undo and no conflict path
The hypothesis writes into `gui2/data/pass1_auto_<book>.json`, which is a git-tracked file the owner edits in Pass1 Auto. When the pull runs, a word silently disappears from the queue the owner is looking at, and—if gui2 is *not* open—into a file he has uncommitted changes on. A `git pull --ff-only` in the nightly window then fails on the dirty tree, and the local deletion is invisible until he diffs. Worse, the pull deletes on the strength of an *untrusted* server file, and that deletion is then committed by the owner's data update — a contributor can delete any word from the owner's queue, permanently, with one edit to their list. Fix: the pull should not edit tracked files. Write the words to an ignored `gui2/data/pass1_auto_tainted.json` (or similar) and have `Pass1FileManager.read` on the laptop subtract that set, showing "N hidden from contributors" — the same mechanism the server already uses. Deletion stays a deliberate act, with a button and a message.

## 3. Major — the contributor sees the wrong count and a word that re-appears on the next load
`gui2/pass1_file_manager.py:47-51` filters only the caller's own list; `pass1_add_controller.py:88-96` sets the remaining count from a fresh read but then iterates `auto_processed_dict_copy`, a snapshot taken at `load_json` (`:77-78`). Scenario: alice opens book `mn`, sees 40. bob finishes 3 words while she is working. Alice's counter still says 40, and she is still offered bob's 3 words — she saves them a second time, writing duplicate `additions_alice.json` entries that the reconcile then has to sort out. Fix: intersect every contributor's list into `_read_view` and re-take the snapshot on each `get_next_item`.

## 4. Major — "deleted" is a lie, and there is no message when the shared list changes the view
`pass1_add_controller.py:283` says `f"{self.word_in_text} deleted"` on the server, where nothing was deleted — a one-word entry was appended to a file the contributor has never seen and cannot open. And when another contributor's removal hides a word from the queue, the counter drops between two clicks with no explanation. Fix: on a contributor, say `"<word> finished and hidden from the shared queue"`, and when another user's removal hides something, add a one-line note (`"3 words hidden: added by bob, carol"`) when the book is loaded.

## 5. Major — no trace exists for either direction
`contrib_pull.py:319-323` logs one line per run; the removal application would be the only step that mutates a tracked file, and it is unlogged. If a word is wrongly removed the owner has: a `git diff` and no reason. If a word is *not* removed (bad file, dropped user, `editor_running`, `already done today`), the counter is the only symptom. Nothing records which user removed which word from which book when. Fix: append to `logs/contrib_pull.log` one line per applied removal — `2026-11-12 removed mn:kāya from alice (bob also listed)` — and add `pass1_removals: 12 applied, 0 skipped` to the `Status` text (`contrib_pull.py:327-345`) so the owner sees it in `just contrib-pull` and in the notice. Two conflict cases need their own line: a word listed by two users, and a word no longer in any tracked file (stale list).

## 6. Nit — the server list grows forever
`pass1_file_manager.py:73-82` never prunes. Within a year the laptop globs dozens of `pass1_auto_removed_*.json`, most for words long gone. Not a blocker, but a `prune` step in the pull (drop entries no longer in any tracked file, rewrite) keeps the observable surface small — as long as each dropped entry is logged first.

## 7. Nit — the status/notice vocabulary hides the new step
`contrib_pull.py:180-186` will report `pulled 5 files, 12 entries` — the removals count is not an "entry" and inflates the number the owner reads. Count them separately.


### g1_migration_debt

`book` comes from a dropdown of known books, so the path-injection concern is narrow — but the *removed list's* book keys come from a contributor file, which is the real hazard.

## Findings

**1. Blocker — the pull must not let a contributor's file name a book.**
`gui2/pass1_file_manager.py:24` builds the tracked path as `gui2_data_path / f"pass1_auto_{book}.json"`, and `:33-36` (proposed) would take `book` from a contributor's `pass1_auto_removed_*.json` keys. Keys like `../../db_tools/data/dpd.db`, `../data/pass1_auto_x`, or `x/../../../etc/...` escape `gui2/data`. A laptop-side delete loop reading those keys unlinks or rewrites arbitrary files as the owner. The proposed "delete words from tracked files" pump makes contributor input a filesystem selector.
Fix: never derive the path from the JSON. Iterate `gui2_data_path.glob("pass1_auto_*.json")`, take the book from the *filename*, and look the key up in the dict; drop keys with no matching tracked file (log them). Also validate the word is a `str` before `data.pop`.

**2. Blocker — the deletion will fight git, not carry it.**
The hypothesis says the owner's "normal data commit" carries the deletion to main (`scripts/server_contrib/maintenance_window.py:110`, `git pull --ff-only`). But `contrib_pull.py:505` refuses to run while gui2 is open (`editor_running`), and the owner edits in gui2 — so a pulled deletion only reaches a tracked file the owner later hand-commits. If `pull` does the deleting and the owner does *not* commit `gui2/data/pass1_auto_*.json` that day, the file sits dirty; the next `git pull --ff-only` at the nightly window and the owner's `git pull` both fail on a dirty tracked file, or the deletion is silently reverted by a later checkout/`--force` path (`contrib_push.py:71`, `checkout -f -B`).
Fix: make the pull write through `Pass1FileManager` and emit an explicit "tracked data files changed, commit them" line in `Status.text()`; or state in the spec that the owner must commit `gui2/data/pass1_auto_*` before any further `git pull`, and have the pull refuse to delete if `git status --porcelain gui2/data/pass1_auto_*` is dirty.

**3. Major — a re-run of Pass1 Auto resurrects the words.**
`gui2/pass1_auto_controller.py:419`-ish Pass1 Auto `write`/`update` replaces the whole book file from the current CST list. Nothing consults the removed lists. So after the pull deletes words from the tracked file, the next Pass1 Auto run on that book puts them back, the owner re-adds them, and the loop documented in the brief repeats forever. The pull-side deletion is a one-shot patch, not a state.
Fix: keep a durable laptop-side set (the existing `gui2/data/pass1_auto_removed_*.json` are gitignored and already the right shape) and have Pass1 Auto's writer subtract it. Without that, this change buys one day.

**4. Major — growing forever, with no pruning in scope.**
`gui2/pass1_file_manager.py:74` appends on every save and nothing ever removes an entry (`read` only subtracts). Contributor lists grow for the life of the account, and the pull must read and union every contributor's file daily. The scope explicitly excludes pruning, so this debt is created, not paid.
Fix: have the pull prune a list once its words are absent from *every* tracked file, and write the pruned list back — that is the only writer, so it needs no protocol.

**5. Major — one bad contributor file drops all their files; a JSON-kind check already exists but the new kind fits none.**
`contrib_pull.py:139` `JSON_KINDS = ("additions", "corrections")`; `_check_json` (`:151`) requires *every value to be a dict*. A removed list is `{book: [word, ...]}`, so if `pass1_auto_removed` is added to `DELIVERED_KINDS` and to `JSON_KINDS`, every list is rejected as "a JSON entry is not an object". If it is added to `DELIVERED_KINDS` only, it gets `_check_lines` on a JSON file and fails "no final newline". Either way the contributor's *entire* delivery is dropped by `remove_users` (`:255`).
Fix: a third check for this kind (dict of `str -> list[str]`, each word a `str`, size cap), in `check_content`.

**6. Major — `DELIVERED_KINDS` is the push's copy list.**
`contrib_push.py:80` copies every matched kind into the `contributions` branch with `git add -f`. Adding the removals kind means the daily branch commit now carries pass1-removal data into main on every window, in a path (`gui2/data/pass1_auto_removed_<user>.json`) that `.gitignore:106` deliberately excludes. The reconcile log has no entry for it either (`contrib_reconcile.py:63` `LINE_KINDS`), so re-uploads are re-committed every night.
Fix: keep the pull's own small allowlist for this kind; do not put it in `DELIVERED_KINDS`.

**7. Nit — `remove` returns a view built before the append is visible.**
`gui2/pass1_file_manager.py:87` returns `self._read_view(book)` after writing; harmless, but `_read_removed` re-reads from disk each call (`:27`), so every keystroke-save is two full reads of a file that grows forever.

**8. Nit — no rollback for the deletion.**
`maintenance_window.py:118` captures a rollback for the server; the laptop's tracked-file deletion has none. `git checkout -- gui2/data/pass1_auto_*.json` is the fix, but only if the file was committed first (see #2).
