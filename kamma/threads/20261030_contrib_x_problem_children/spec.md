# Spec: contributor problem children (placeholder)

**Thread:** 20261030_contrib_x_problem_children
**Date:** 2026-10-30
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Status:** PLACEHOLDER. A list of problems found during the live test of
`20261023_contrib_2_edits_json`. Nothing here is decided or scheduled. Each
item needs a look, and a decision from the user, before any fix.

## Problems found

### 1. `flet run` starts the app in the wrong folder (verified)
`uv run flet run --web -p 8551 gui2/main.py` moves the app into
`gui2/.flet/storage/data`. `ProjectPaths` uses the current folder
(`Path(os.path.abspath("."))`), so the first data file read failed:
`[Errno 2] No such file or directory: '.../gui2/.flet/storage/data/tools/cst_book_translator.tsv'`.
What worked: `FLET_FORCE_WEB_SERVER=true FLET_SERVER_PORT=8551 uv run python gui2/main.py`.
That command also served the page on 127.0.0.1:8551.
The broken command is written in other threads and may also break on the server:
- `20261023_contrib_1_web_server`: `spec.md:73`, `plan.md:214`
- `20261023_contrib_3_preview_before_save`: `plan.md:58`, `spec.md:72`
- `20261023_contrib_4_temp_server_test`: `plan.md:69`, `spec.md:70`
- `20261023_contrib_5_hardening`: `plan.md:260`
- `gui2/README.md:21` (that line is for the desktop dev reload, probably fine)
Not checked: whether `flet run` fails the same way on the server. The server
thread should use the `python gui2/main.py` form, or prove `flet run` works there.

### 2. Clipboard error in the browser (verified, cause not proven)
After a Pass2Add save, the page showed
`PlatformException(copy_fail, Clipboard.setData failed., null, null)`.
The save itself had worked (the JSON was written). The error came from
`await ft.Clipboard().set(...)` in `gui2/pass2_add_view.py` (~line 991, also ~1264).
It cut off the steps after it (history list, daily log) for that save. It stopped
after the user allowed clipboard access in the browser. Open questions:
- Does the server page (https, other browsers) fail the same way?
- Pass1Add copies with `pyperclip.copy` (`gui2/pass1_add_controller.py:123`).
  `pyperclip` writes the SERVER clipboard and fails if the server has no
  clipboard tool. Not tested headless. Worked on the desktop.
- A clipboard failure should not cancel the rest of a save.

### 3. Pass2 checks were written for tabs a contributor will not see
Plan 3.1 of `contrib_2_edits_json` tested Pass2 edit, correction and delete.
`contrib_5_hardening` hides Pass2 from contributors. Two checks were never run
in the app: an edit of a plain db word (a correction), and the refusal to delete
a plain db word. Only unit tests cover them. If Pass2 is ever opened to
contributors, run both live.

### 4. A contributor id can equal a real db id (verified once)
`get_next_id` gave alice's test addition the id 90368. The next real word that
user 1 added to the db also got 90368. This is the "id clash" the
contrib_2 spec lists as an assumption. The nightly merge and the reconcile
step must handle it. A test with a real merge of two such entries is missing.

### 5. Post-save "add the parts" dialog in Pass2 (not a defect, check scope)
After a Pass2 save, a dialog offers to queue the construction parts as new
words. It is an old feature. In a contributor session the queued words go to
the Pass2 queue files, which are shared. Not checked.

### 6. Small items from the contrib_2 phase gates
- `checked_alice.csv` got the same word twice (Sandhi OK and Add to Sandhi both
  write it). The shared file behaves the same way. Probably harmless.
- `Pass1AddController.additions_manager` is now unused.
- `UsernameManager.is_not_primary()` is True when the username is None (desktop
  first run before the dialog). Such a session saves to JSON only.
- `pyright --project /dev/null` reports about 100 flet-typing errors in gui2
  files, and `item_to_history` is "possibly unbound" in `pass2_add_view.py`
  (~852-865). Both were there before. gui2 is excluded from the pre-commit pyright.
- The per-user files (`user_dictionary_*.txt`, `checked_*.csv`,
  `manual_corrections_*.tsv`, `variant_readings_*.tsv`, `spelling_mistakes_*.tsv`)
  are not sent by the nightly push yet (`contrib_push.py`).

## Added by the review of `20261023_contrib_2_edits_json` (2026-10-30)
Three independent reviews (Sonnet subagent, DeepSeek via pi, CodeRabbit) found these.
The ones fixed in contrib_2 are listed in its `review.md`, not here.

### 7. Other tabs still write `dpd.db` for a contributor (both reviewers, verified in code)
`gui2/main.py` builds all 17 tabs for every user. These tabs write the real db:
DB tab (`gui2/filter_component.py` `_save_changes`), Sandhi find/replace,
Spelling find/replace, sandhi contraction utility, Roots, Compound types,
Inflection templates. The contrib_2 spec filed them as "primary-only, KEEP". That
is wrong until `contrib_5_hardening` hides them. Its tab table covers them, but
check each write path is really behind a hidden tab. A cheap backstop to
consider: refuse in `DatabaseManager`'s write methods when the user is a contributor.

### 8. Pass2 "additions" / "corrections" buttons delete a contributor's own edits (verified)
`get_next_addition` and `get_next_correction` `.pop()` from the live dicts. For a
contributor those dicts are the overlay and the only record. The next save writes
the shortened dict. Hidden once Pass2 is hidden (contrib_5). If Pass2 is ever
opened to contributors, hide or refuse these buttons, and the X, eg and new-word
buttons, for non-primary users.

### 9. Smaller items
- `is_not_primary()` (save seam) and the `resolve_username() or "1"` value (paths,
  overlay) disagree when no username is set. The save goes to JSON while the
  paths and overlay act as user 1. Make both use one value.
- Overlay: a correction that renames `lemma_1` still returns the old db row for the
  old lemma. `update_db_fields` keeps old form values for columns missing from an
  old JSON entry. Neither is tested.
- `get_next_id` raises on a non-numeric `id` in a hand-edited additions file.
- `variants.py` / `spelling.py` write no header row when the shared file is
  missing (headers come only from the shared file).
- `request_dpd_server` still runs for a contributor save. The local webapp does
  not hold the JSON-only word.
- The DB tab duplicate-lemma check (`filter_logic.find_duplicate_lemma_1`) ignores the overlay.
- CodeRabbit (not this thread): `rename_pattern_in_headwords` in
  `gui2/database_manager.py` does not call `mark_corpus_stale()` (added in a56f3762, #273).
- Not covered by any test: the Pass2 view methods `_has_own_edit` / `_discard_own_edit`,
  and a full chain (save, overlay shows it, re-edit stays an addition, discard).

