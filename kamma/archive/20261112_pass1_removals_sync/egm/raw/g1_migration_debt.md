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