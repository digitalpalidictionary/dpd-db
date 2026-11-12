# Brief — 20261112_pass1_removals_sync (GitHub issue #215)

## Request (owner, 2026-11-12)
- In gui2 the owner sometimes runs Pass1 Add (on the laptop).
- Sometimes a contributor runs Pass1 Add on the contributor web server.
- If words get added from any Pass1 Auto file, they should be removed from the local or web server.
- Find a nice simple solution, nothing complicated.

## Verified facts (read from the source on 2026-11-12)
1. Pass1 Auto runs on the laptop only. It writes `gui2/data/pass1_auto_<book>.json` (one dict per book, `{word_in_text: {field: value}}`). These files are tracked by git and reach the server through git (`kamma/tech.md`, "Pass1 Auto context").
2. `gui2/pass1_file_manager.py` `Pass1FileManager.remove(book, word)`: on the laptop (user "1", `removed_path is None`) it deletes the word from the tracked file. For a contributor it appends the word to `pass1_auto_removed_<user>.json` (`{book: [word, ...]}`, atomic write) and never edits the tracked file; `write`/`update` raise `PermissionError` for a contributor.
3. `Pass1FileManager.read(book)` for a contributor returns the tracked file minus that contributor's OWN removed list only.
4. `gui2/paths.py` `Gui2Paths.for_user`: every contributor's per-user files, the removed list included, live in ONE shared folder `DPD_GUI2_DATA_DIR` = `/var/lib/dpd/contrib_data` on the server (`scripts/server_contrib/add_contributor.sh:52`).
5. `gui2/pass1_add_controller.py` `_save_previewed_word` calls `remove_word_and_save_json` after every committed save of the book word. Pass1 Add shows every word in the book file; it does not check whether the word is already in `dpd.db`.
6. A contributor's save never touches the server db: `gui2/save_router.py` sends it to `additions_<user>.json`. The daily laptop pull (`scripts/server_contrib/contrib_pull.py`, systemd timer, skips while gui2 is open) copies the delivered contributor files into `gui2/data` and merges the flag files.
7. The pull copies only names matching `DELIVERED_KINDS` in `tools/contrib_entry.py` (8 kinds). `pass1_auto_removed_*.json` is not one of them, so the removed lists never reach the laptop. This gap was noted in `kamma/archive/20261030_contrib_x_problem_children/spec.md:236`.
8. `DELIVERED_KINDS` is also read by `contrib_push.py` (copies every kind to the `contributions` branch with `git add -f`), `contrib_reconcile.py` and `merge_contrib_files.py` (both act only on kinds they name). `contrib_pull.py::_check_json` rejects a JSON kind whose values are not dicts, and a rejected file drops ALL of that contributor's files.
9. The `just contrib-merge` branch flow is marked "Replaced by contrib-pull. Do not run both." The daily pull is the live channel.
10. Laptop → server already works: the laptop deletes the word from the tracked file; the owner's "data update" commits (8 between 2026-11-04 and 2026-11-11) carry it to main; the nightly window (`maintenance_window.py`) runs `git pull --ff-only` then reconcile.
11. No code globs `pass1_auto_*.json`; `.gitignore` already ignores `gui2/data/pass1_auto_removed_*.json`.

## Anchored hypothesis
A word a contributor adds from a Pass1 Auto book goes only into that contributor's private removed list. The laptop never learns of it, so the owner can add it again, and other contributors still see it. Fix: (1) the daily pull also fetches every `pass1_auto_removed_<user>.json` and deletes those words from the laptop's tracked `pass1_auto_<book>.json` files; the owner's normal data commit then carries the deletion to the server. (2) On the server, a contributor's view hides the words in every contributor's removed list (one shared folder), not only their own. Scope: the pull, `Pass1FileManager`, tests. No db check, no git write on the server, no pruning of the lists.
