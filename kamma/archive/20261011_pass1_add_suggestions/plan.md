# Plan: Pass1Add AI suggestions go to the `_add` column

Spec: `kamma/threads/20261011_pass1_add_suggestions/spec.md`

## Architecture Decisions

- **Reuse the shared `DpdFields` methods** (`add_to_ui(include_add_fields=True)`,
  `update_add_fields`, `clear_fields(target="add")`). Nothing is copied from
  `gui2/pass2_add_view.py`. Pass2Add's code is the reference, not a source.
- **The split lives in `Pass1AddController.load_into_gui`.** It is the only place
  that loads JSON data into the fields. A module-level constant in
  `gui2/pass1_add_controller.py` names the four source-text keys
  (`example_1`, `translation_1`, `example_2`, `translation_2`). These are the
  keys `gui2/pass1_auto_controller.py::update_auto_processed` copies from the
  source text.
- **No change to `gui2/dpd_fields.py` behaviour.** Only the stale comment at the
  `compound_type_add` `is_mounted` guard is reworded. The guard stays.
- **No "copy all" button, no logging, no Pass1Auto change** (see spec "not included").
- **Checkpoints are report-only.** The user commits at the end (project rule).
  Stage by explicit file list. Never use whole-tree git commands.

## Phase 1 — Load split

- [x] 1.1 Write `tests/gui2/test_pass1_add_controller.py` (new file). Build the
  controller with `object.__new__(Pass1AddController)`, like
  `tests/gui2/test_pass2_add_component_words.py`. Give it a fake `ui` with
  `word_in_text` (a `SimpleNamespace` with `value` and a no-op `update`), a
  `page` with a no-op `update`, and `dpd_fields` that holds real-ish `fields`
  (`SimpleNamespace(value=None)` per name) and records `update_add_fields` calls.
  Monkeypatch `open_in_goldendict` and `pyperclip.copy` in the controller module.
  Feed `sentence_data` with AI keys, the four source-text keys, and one unknown
  key. Assert:
  - every AI key's main field is still empty (`None`);
  - `update_add_fields` got exactly the AI keys, values included, and no
    source-text keys;
  - the four source-text main fields hold their values.
  → verify: `uv run pytest tests/gui2/test_pass1_add_controller.py` FAILS on the
  current code (main `lemma_1` is set, `update_add_fields` is never called).
  Paste the failure output here.
  RESULT (pre-fix): `test_ai_keys_go_to_add_fields_only` FAILED —
  `AssertionError: assert 'narena' is None` (main `lemma_1` filled directly).
  `test_source_text_keys_fill_main_fields` passed (current behaviour, kept).
  Baseline before this thread: `uv run pytest tests/gui2/` → 364 passed.
- [x] 1.2 Change `load_into_gui` in `gui2/pass1_add_controller.py`: source-text
  keys that are fields go to the main fields. Pass all other keys to
  `self.ui.dpd_fields.update_add_fields(...)`. That method skips unknown keys
  and calls `page.update()` itself. Keep `open_in_goldendict`, `pyperclip.copy`,
  and the `word_in_text` update as they are.
  → verify: the 1.1 test passes. Then revert only the split, re-run, and record
  how many assertions fail. Restore the split in the same command.
  RESULT: with the fix, 2 passed. With the split reverted (old direct-fill loop),
  1 failed (`assert 'narena' is None`), 1 passed. Restored → 2 passed.
- [x] 1.3 Phase check.
  → verify: `uv run ruff check --fix`, `uv run ruff format`, and `uv run pyright`
  are clean on both files. `uv run pytest tests/gui2/` passes. Report only; no commit.
  RESULT: ruff clean, format unchanged, pyright 0 errors. `tests/gui2/` 366 passed.

## Phase 2 — Mount the column and fix the knock-on effects

- [x] 2.1 `gui2/pass1_add_view.py::_build_middle_section`: pass
  `include_add_fields=True` to `add_to_ui`, keeping `visible_fields=visible_fields`.
  → verify: `uv run pyright gui2/pass1_add_view.py` clean. The live check is in 3.1.
- [x] 2.2 `gui2/pass1_add_controller.py::make_dpd_headword_and_add_to_db`: the
  message after the next item loads uses `self.word_in_text`, not
  `self.ui.dpd_fields.fields['lemma_1'].value`. Read the function first. The
  `20261007_preview_before_save` thread may have changed it.
  → verify: add a test to `tests/gui2/test_pass1_add_controller.py` only if it
  is cheap with the 1.1 fakes. Otherwise rely on live check 3.1 step 4.
- [x] 2.3 `gui2/pass1_add_view.py::_handle_history_selection`: after the
  headword is found and before the main fields are written, call
  `self.dpd_fields.clear_fields(target="add")`. Note: `clear_fields` also calls
  `flags.reset()`. That is right here, because a different word is now loaded.
  → verify: pyright clean. The live check is in 3.1 step 5.
- [x] 2.4 `gui2/dpd_fields.py`: reword the comment above
  `if is_mounted(compound_type_add_field):`. The current text says "Pass1Add
  never mounts the `_add` shadow fields". New text: the row can be hidden or
  unmounted, and in 1.0 `update()` on an unmounted control raises. Do not
  change code.
  → verify: `git diff gui2/dpd_fields.py` shows only comment lines.
- [x] 2.5 Phase check.
  → verify: ruff check, ruff format, and pyright are clean on every touched
  file. `uv run pytest tests/gui2/` passes. `just typecheck` passes. Report only.
  RESULT: ruff clean, format unchanged, pyright 0 errors on all four files.
  `tests/gui2/` 366 passed. `just typecheck` 0 errors. `git diff gui2/dpd_fields.py`
  is one comment line. 2.2 has no unit test (it would need the whole save path
  faked); live check 3.1 step 4 covers it.

## Phase 3 — Live verification

- [x] 2.6 *(User request, 2026-10-11.)* `gui2/pass1_add_view.py`: rename the
  button "Add to Spelling mistakes" to "Add to Spelling" so it fits on one line.
  → verify: ruff and pyright clean; `rg "Spelling mistakes" gui2/` finds no
  button label. RESULT: clean; only a comment in `sandhi_view.py` remains.
  Button look to be confirmed by the user on the next GUI start.
- [x] 3.1 Live run with the user (`cd /home/bodhirasa/MyFiles/3_Active/dpd-db && just gui`):
  1. Open Pass1Add. Process a book that has Pass1Auto output. Each visible row
     shows ← and a grey/red suggestion.
  2. The main fields are empty, except the example and translation fields.
  3. Click ← on two fields. Only those main fields fill.
  4. Add to DB. The db row holds only the copied values plus the examples.
     The message names the next word in the text.
  5. Pick a word from History. The suggestion column empties and the main
     fields show the history word.
  6. Clear All, Pass, and Delete still work. The next word shows fresh suggestions.
  → verify: the user confirms each step. Record the results here.
  RESULT (2026-10-11): user tested, "all good". Saved `sumanadevīvatthu`
  id 90246, origin `pass1`. The db row differs from the AI response
  (`temp/prompts/pass1/sumanadevīvatthu_response`) where the user edited:
  meaning_2 trimmed, construction/family_compound changed, stem/pattern
  `sumanadevīvatth` / `u nt` instead of the AI's `-` / empty. So only the
  user's values were saved, not the raw suggestions.
## Phase 4 — Review fixes (2026-10-11)

Review ran as two parallel Sonnet subagents: a from-scratch spec/code audit,
and CodeRabbit (`coderabbit review --agent --uncommitted --include-untracked`,
once with `--dir gui2` and once with `--dir tests/gui2`).

- [x] 4.1 CodeRabbit (major): History load used `clear_fields(target="add")`,
  whose `flags.reset()` lets the blur helpers overwrite the saved
  stem/pattern/lemma_2. This was a regression from task 2.3. Fix in
  `gui2/pass1_add_view.py::_handle_history_selection`: clear with
  `update_add_fields({config.name: "" for config in field_configs})`, which
  leaves the flags alone. New test `tests/gui2/test_pass1_add_view.py`.
  → verify: 2 passed. With the fix reverted to `clear_fields`, 1 failed
  (`stem_pattern_done` is False). Restored → 2 passed.
- [x] 4.2 Sonnet audit (should-fix): Process Book loaded the first word without
  clearing the form, so stale `_add` values could remain. Fix: `process_book`
  in `gui2/pass1_add_controller.py` calls `self.ui.clear_all_fields()` first.
  → verify: no unit test (it would only assert the call happens). Live check
  in 4.4.
- [x] 4.3 Sonnet nits: spec "rebuild" claim now names Process Book; the test's
  fake-`DpdFields` limit is accepted.
  → verify: the spec is updated. ruff, format, and pyright are clean on all
  five files. `tests/gui2/` 368 passed. `just typecheck` 0 errors.
- [x] 4.4 Live re-check by the user (`cd /home/bodhirasa/MyFiles/3_Active/dpd-db && just gui`):
  (a) the spelling button fits on one line; (b) load a History word, tab
  through stem and pattern, and the saved values stay; (c) Process Book while a
  word is loaded gives a clean form with fresh suggestions.
  → verify: the user confirms.
  RESULT (2026-10-11): user confirmed "all checks out".

- [~] 3.2 Run `graphify update .`.
  NOTE: started 2026-10-11, still running at finalize (graph.json is 1.2 GB). Left running in the background; it does not affect the code.
  → verify: the command exits 0.
