# Spec: contributor edits kept in JSON, shown on top of the db

**Thread:** 20261007_contributor_edits_json
**Date:** 2026-10-07
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215)
(third round; commits reference `#215`)
**Builds on:** `kamma/threads/20260719_contributor_web_server/` — read its spec
first. This thread CHANGES that spec's point 4 (contributors no longer write
the db).
**Sibling threads (planned 2026-10-07, same discussion):**
- `20261007_preview_before_save` — runs AFTER this thread (edits the same two
  save handlers; never run both in the same working tree at once).
- `20261007_temp_server_test` — runs in parallel; its live checks wait for
  this thread and the preview thread.

## Overview

gui2 will run on a server for contributors, one gui2 web instance per
contributor (decided in 20260719; unchanged). This thread does two things:

1. Closes the last shared-file gaps a contributor session can write.
2. Stops contributor saves writing the db. A contributor's edits live ONLY in
   their JSON files, and what they see is "db + my own edits" for the words
   they edited.

The maintainer (username "1") keeps writing the db exactly as today. Both
users go through one save function, so there is one code path.

## Decisions made (2026-10-07, do not relitigate)

- Contributor edits never go into the db. JSON is the only record.
- A contributor's Delete only discards their own JSON edit/addition for that
  word. They cannot delete a real db word. (User choice 3A.)
- One process per contributor stays (20260719). Username/role come from
  `DPD_GUI2_USERNAME` / `DPD_GUI2_ROLE` env vars, config.ini fallback
  (`gui2/user.py::resolve_username`, `tools/server_mode.py::resolve_role`).
- Whole-db views (DB tab, Tests tab, families lists, relationship detector,
  Pass2Pre/Auto) do NOT show contributor edits. Accepted.

## Current behaviour (verified by reading the code, 2026-10-07)

### Per-user files
`Gui2Paths.for_user` (`gui2/paths.py`) already routes 10 files per user for
any username other than "1": additions, additions_added, corrections,
corrections_added, daily_log, history, filter_presets, headword_stash,
example_stash, commentary_stash. "Last example" and "last commentary"
(`gui2/dpd_fields_examples.py`, `gui2/dpd_fields_commentary.py`) are stored
inside the example stash (`gui2/example_stash_manager.py`), so they are
already per-user.

A full sweep of file writes in `gui2/` and in the `tools/` modules gui2
imports (rg for `json.dump|write_text|open(...,'w'|'a')|to_csv|config_update`)
found these still shared and reachable by a contributor:

| Write | Where | Verdict |
|---|---|---|
| `shared_data/user_dictionary.txt` | `tools/spelling.py` `CustomSpellChecker.add_to_dictionary`, called from the meaning field (`gui2/dpd_fields_meaning.py:123`) | **FIX** — per-user file. The spelling gate blocks save, so contributors need this button. Two processes rewriting one file race (the lock is per process), and the server never pushes this file back. |
| compound types / phonetic changes TSV "edit" buttons | `gui2/dpd_fields.py` `_click_edit_compound_types`, `_click_edit_phonetic_changes` → `open_tsv_for_editing` (opens a desktop editor) | **FIX** — refuse in server mode, gated at the source like `tools/goldendict_tools.py::open_in_goldendict` |
| `pass1_auto_{book}.json`, `pass2_*` queue files | queue managers | **KEEP** — 20260719 decision C: different books per contributor |
| `speech_marks.json` | only `regenerate_from_db` writes (manual button) | **KEEP** — rebuilt from db, holds no user data |
| temp prompt files (`temp/prompts/...`) | pass1_auto / pass2_auto debug | **KEEP** — throwaway, keyed by word |
| decon / see / proofreader / roots / compound-type tab files | primary-only tabs | **KEEP** — not contributor work |
| `shared_data/deconstructor/checked.csv`, `manual_corrections.tsv`, `variant_readings.tsv`, `spelling_mistakes.tsv` | Pass1Add buttons "Sandhi OK", "Add to Sandhi", "Add to Variants", "Add to Spelling" (`gui2/pass1_add_view.py`, `gui2/mixins.py::SandhiOK`, `gui2/sandhi_files_manager.py`, `gui2/variants.py`, `gui2/spelling.py`) | **FIX (added 2026-10-11, user choice A)** — the first sweep wrongly filed these under "primary-only tabs". A contributor can click all four. Each write goes to one shared file, and the variants/spelling writers rewrite the whole file, so two processes race. The server never pushes these files back. |
| `config.ini` username | first-run dialog only (`gui2/user.py`) | **KEEP** — the server sets the env var |

`CustomSpellChecker()` is built with no args at `gui2/dpd_fields.py:70` and
`gui2/filter_component.py:115`. Its file is `ProjectPaths().user_dict_path`
(`tools/paths.py:699`).

### Save flows
- **Pass1Add:** `gui2/pass1_add_controller.py::make_dpd_headword_and_add_to_db`.
  Checks (db loaded, spelling, duplicates), then a db add (new word) or a db
  update (re-edit from history). For a non-primary NEW word it also calls
  `add_additions`. **A contributor re-edit writes NO JSON today** — a bug that
  the save seam fixes. Then `request_dpd_server`, history, daily log, clear,
  and load the next item.
- **Pass2Add:** `gui2/pass2_add_view.py::_click_add_to_db` (update/add block
  at lines ~826-852). It calls `update_word_in_db` or `add_word_to_db`, plus
  additions/corrections JSON for non-primary. Then the post-save steps:
  history, daily log, pass2_auto removal, and the processed
  addition/correction (user 1's review queue).
- Once db writes stop, a contributor re-editing their OWN new word in Pass2
  would hit `update_word_in_db` → "Word not found". The save seam + overlay
  fixes this.
- Contributor JSON writers: `AdditionsManager.add_additions` and
  `CorrectionsManager.update_corrections` key entries `{username}_{id}` and
  dedupe by id (`_key_for_id`). Each entry is the word's column dict plus
  `comment`.

### Reads
Every single-word load in the editing tabs goes through
`DatabaseManager.get_headword_by_id` / `get_headword_by_lemma` /
`get_headword_by_id_or_lemma` (`gui2/database_manager.py:653-670`). Callers:
pass2_add_view (7 sites), pass1_add_view (2), pass2_auto_control (2),
dpd_fields (1, the duplicate check). Duplicate checks use `get_headword_by_id`
and `db.all_lemma_1` (`gui2/dpd_fields.py::validate_no_duplicates`). New ids
come from `get_next_id` (db max + 1). `make_dpd_headword_from_dict`
(`gui2/dpd_fields_functions.py:352`) builds a transient `DpdHeadword` from a
dict and skips keys that are not attributes.

### Delete
Pass2Add Delete: `_click_delete_from_db` → confirm dialog → `_click_delete_ok`
→ `delete_word_in_db` (`gui2/pass2_add_view.py:974-1031`).

## What it should do

### A. Remaining per-user files
1. `Gui2Paths` gains `user_dictionary_path`. User 1 → the shared
   `shared_data/user_dictionary.txt` (unchanged). Contributor →
   `gui2/data/user_dictionary_{u}.txt`.
2. `CustomSpellChecker` takes an optional per-user file. It always loads the
   shared dictionary and also loads the per-user file. `add_to_dictionary`
   writes only to the per-user file when one is given. User 1 is unchanged.
3. The two "edit TSV" buttons refuse in server mode with the message "not
   available on the server".

### A2. Pass1Add helper buttons: per-user files (added 2026-10-11)
3b. `Gui2Paths` gains four paths: sandhi checked, sandhi corrections, variant
   readings, spelling mistakes. User 1 → the shared `shared_data/deconstructor/`
   files (unchanged). Contributor → `gui2/data/<name>_{u}.<ext>`.
3c. A contributor's four buttons write ONLY their own files. The shared files
   are never touched by a contributor session.
3d. A contributor's own entries still take effect for them: the Pass1Auto and
   Pass2Pre skip lists read shared + own (variants, spelling mistakes, sandhi
   checked). User 1 reads the shared files only, as today.
3e. Getting these four files from the server to the maintainer is NOT done here
   (the server thread must add them to the nightly push — see Not included).

### B. One save seam
4. One function decides where a save goes:
   - User 1 → db, exactly as today (`add_word_to_db` / `update_word_in_db`).
   - Contributor → JSON only. An existing id in their own additions →
     `add_additions`. Any other existing id → `update_corrections`. A new word →
     `add_additions`. No db write. Returns `(True, "")` after the JSON write.
5. Pass1Add and Pass2Add both call the seam instead of their own db/JSON
   code. All post-save steps stay as they are.

### C. Overlay: db + own edits (contributors only)
6. `DatabaseManager` gets an optional overlay that the ToolKit sets only for
   contributors. With it set:
   - `get_headword_by_id` / `get_headword_by_lemma` return the user's own JSON
     entry as a transient `DpdHeadword` when one matches (corrections first,
     then additions). Otherwise they return the db row.
   - `all_lemma_1` includes the lemmas of the user's own additions, for the
     duplicate check.
   - `get_next_id` = max(db max id, own additions' max id) + 1.
7. User 1: no overlay, behaviour unchanged.

### D. Contributor delete
8. Pass2Add Delete for a contributor: if their own JSON holds an entry for
   this id, confirm, remove it, then reload the word from the db (or clear the
   form for an addition). Otherwise show "you can only discard your own
   edits". User 1's delete is unchanged.

## Assumptions & uncertainties

- **Id clash after a rebuild:** a contributor addition's id may later be taken
  by a real db word on main. 20260719's absorption invariant (no rebuild until
  main's contributor JSONs are empty) + reconcile keep this safe. With the
  overlay the server db is never written, so a rebuild cannot lose work.
- **JSON value types:** entries come from `vars(word)`, so ints stay ints and
  strings stay strings after a JSON round trip. Assumed safe for
  `make_dpd_headword_from_dict`. Verified by the overlay tests.
- **Callers that compare `headword_original` with the saved word**
  (`is_existing_word` in Pass2) get a transient object from the overlay. They
  compare `.id` only (read: `pass2_add_view.py:817-824`). Other callers that
  use relationships (`.rt`, `.fr`) on a loaded word were not all read. A
  transient object returns None for them. The executor checks every
  `get_headword_by_*` caller listed above.
- The per-user spelling file is NOT pushed by `scripts/server_contrib/contrib_push.py`
  (it only sends additions/corrections). The maintainer adds such words
  himself if his review flags them.

## Constraints

- User 1: behaviour byte-identical.
- Never mutate a session-attached ORM object. Overlay objects are transient
  and never added to a session.
- Gate contributor behaviour on `UsernameManager.is_not_primary()`. Gate
  server-only behaviour on `tools/server_mode.is_headless_server()`.
- Project rules: ruff check --fix, ruff format, pyright
  (`uv run pyright --project /dev/null <file>` for gui2/ and tests/ files,
  which are pyright-excluded) and related pytest on every touched file.
  `just typecheck` at the end. Modern type hints, pathlib, no `__init__.py`
  re-exports, `ic` not `print` for debugging.
- No git commands. The user commits. Phase checkpoints are report-only.

## How we'll know it's done

1. Unit tests: per-user dictionary path and write target. Save seam routing
   (user 1 → db; contributor → JSON, zero db calls). Overlay returns own edit
   over db, and plain db otherwise. `get_next_id` / lemma set include own
   additions. `discard` removes only the right entry.
1b. Unit tests: each of the four helper-button writes goes to the per-user file
   for a contributor and to the shared file for user 1; the shared files stay
   byte-identical after a contributor write; the skip lists read shared + own.
2. Live desktop run as user 1: Pass1Add and Pass2Add saves land in the db as
   before.
3. Live local web run as a contributor on a COPY of the db: Save writes only
   the JSON (db row unchanged, checked with sqlite). Reloading the word shows
   their own version. Re-editing their own new word in Pass2 works. Delete
   discards only their own entry. A spelling add goes to the per-user file.
4. Full pytest suite and `just typecheck` pass.

## What's not included

- The preview step (thread `20261007_preview_before_save`).
- Server work (thread `20261007_temp_server_test`; 20260719 Phases 3–4).
- One shared process for many users.
- Showing contributor edits in whole-db views.
- Pushing per-user spelling files upstream.
- Pushing the four per-user sandhi/variant/spelling-mistake files upstream. The
  server thread (`20261007_temp_server_test`, and `contrib_push.py`) must add
  them to the nightly push, or a contributor's flags never reach the maintainer.
