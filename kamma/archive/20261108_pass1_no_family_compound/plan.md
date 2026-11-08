# Plan: remove family_compound from Pass1 Auto and Pass1 Add

GitHub issue: #215 (assumed)
Spec: `kamma/threads/20261108_pass1_no_family_compound/spec.md`

## Architecture Decisions

- **Drop the key in the controller, not just the prompt.** The prompt change stops the AI
  asking for it; one `parsed_json.pop("family_compound", None)` in `update_auto_processed()`
  guarantees no new draft holds it even if a model adds it anyway. No general key filter: the
  controller keeps saving every other key as it does now.
- **One shared list.** Remove the field from `PASS1_FIELDS` only. Pass2 Add's "pass1" filter
  loses it too (owner's choice). No new list.
- **Hidden field stays built.** `DpdFields` still builds `family_compound` in Pass1 Add, hidden.
  This keeps a history-loaded word's value on re-save. No change to `DpdFields`.
- **Old prompt deleted, not edited** (owner's choice). Archived eval scripts stop running; they
  are not repaired.
- **Data rewrite by a throwaway script** in the session scratchpad, using the same `json.dump`
  settings as `Pass1FileManager`, so the diff is deletions only.

## Model Strategy

| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 — Prompt, controller, field list | Fast | Sonnet | Mechanical removals plus one small test |
| 2 — Data files | Fast | Sonnet | Scripted key removal, checked by diff counts |
| 3 — Whole-chain check | Pro | Opus | Judge the sweep for missed carriers before review |

## Phase 1 — Prompt, controller, field list — *Fast*

- [x] 1.1 Add a test to `tests/gui2/test_pass1_auto_controller.py`: set `ctrl.response` to a JSON
  with `"family_compound": "loka nāyaka"`, call `update_auto_processed(None, None)`, assert
  `"family_compound" not in ctrl.auto_processed_dict[word]`. Follow
  `test_example_1_is_the_first_chosen_sentence` (uses `make_controller` and `compile_for`).
  → verify: run `uv run pytest tests/gui2/test_pass1_auto_controller.py -k family_compound`,
  expect 1 FAIL (key still saved). Paste the failure line here.
- [x] 1.2 In `gui2/pass1_auto_controller.py::update_auto_processed()`, right after
  `parsed_json = loads(cleaned_response)`, add `parsed_json.pop("family_compound", None)` with a
  one-line WHY comment (pass1 entries have no `meaning_1`, so the field never shows; too hard
  for beginners).
  → verify: the 1.1 test passes. Then delete the pop line, rerun, expect it to fail, and restore
  the line in the same command. Record "fails without the fix: yes".
- [x] 1.3 In `gui2/pass1_context.py`:
  - remove `"family_compound"` from `ANSWER_KEYS`;
  - remove the `"family_compound"` entry from `related_entry_dict()`;
  - remove it from `_EXAMPLE_ANSWER`;
  - remove the whole `## family_compound` section (6 lines plus blank line) from `_FIELD_RULES`;
  - delete `SYSTEM_PROMPT_OLD`, the `# --- old prompt ---` block and `build_old_prompt()`;
  - change the module docstring's "the old and new prompt builders" to "the prompt builder".
  In `tests/gui2/test_pass1_context.py`: drop the `build_old_prompt` import, delete
  `test_old_prompt_sentence_and_related_lines`, and in
  `test_prompt_lists_answer_keys_and_real_values` add
  `assert "family_compound" not in _prompt("x")`.
  → verify: `rg -n "family_compound|build_old_prompt|SYSTEM_PROMPT_OLD" gui2/` returns only the
  controller pop line from 1.2; `uv run pytest tests/gui2/test_pass1_context.py` passes.
- [x] 1.4 Remove `"family_compound"` from `PASS1_FIELDS` in `gui2/dpd_fields_lists.py`.
  → verify: `uv run python -c "from gui2.dpd_fields_lists import PASS1_FIELDS; assert 'family_compound' not in PASS1_FIELDS"`
  exits 0; `uv run pytest tests/gui2/test_pass1_add_view.py tests/gui2/test_pass1_add_controller.py`
  passes.
- [x] 1.5 Phase check: lint and test every touched file.
  → verify: for each of `gui2/pass1_context.py`, `gui2/pass1_auto_controller.py`,
  `gui2/dpd_fields_lists.py`, `tests/gui2/test_pass1_context.py`,
  `tests/gui2/test_pass1_auto_controller.py`: `uv run ruff check --fix`, `uv run ruff format`,
  `uv run pyright --project /dev/null` all clean. `uv run pytest tests/gui2/` passes (note any
  failure that was there before this thread).

## Phase 2 — Data files — *Fast*

- [x] 2.1 Confirm gui2 is not running (`pgrep -af "gui2/main.py"` as a separate command, read the
  list). If it runs, stop and ask the owner to close it.
  → verify: no gui2 process listed.
- [x] 2.2 Write a scratchpad script that, for each file from
  `git ls-files 'gui2/data/pass1_auto_*.json'` (the five tracked files), loads it with
  `encoding="utf-8"`, pops `family_compound` from every word, and writes it back with
  `json.dump(data, f, ensure_ascii=False, indent=4)` and no trailing newline. Run it with
  `uv run`.
  → verify: `rg -c family_compound gui2/data/pass1_auto_*.json` prints nothing;
  `git diff --numstat -- gui2/data/pass1_auto_*.json` shows 0 added and 314/9/9/8/15 deleted
  (ap/bv/cp/pv/vv), 355 in all; each file still loads as JSON with the same word count.

## Phase 3 — Whole-chain check — *Pro*

- [x] 3.1 Sweep for missed carriers:
  `rg --hidden -n -i "family.compound" gui2/pass1_* gui2/dpd_fields_lists.py tests/gui2/test_pass1_* gui2/data/pass1_auto_*.json gui2/README.md gui2/data/README.md gui2/specs/`.
  → verify: the only hit is the 1.2 pop line and the new tests. Any other hit is fixed or
  explained in this plan.
- [x] 3.2 Run the repo-wide checks.
  → verify: `just typecheck` passes; `uv run pytest tests/gui2/` passes.
- [ ] 3.3 (left to the owner, not run by the agent) Hand the owner one live check: `cd <repo root> && just gui`, open Pass1 Add, load book
  `ap`, confirm there is no `family_compound` row and no `family_compound` suggestion.
  → verify: owner confirms.

## Results (2026-11-08)

- 1.1 failure before the fix: `AssertionError: assert 'family_compound' not in {'lemma_1': 'nara', 'family_compound': 'loka nāyaka', ...}`. Without the pop line the test fails (1 failed); with it, 1 passed.
- 1.5: ruff check, ruff format and pyright (`--project /dev/null`) clean on the 5 files; `uv run pytest tests/gui2/` = 710 passed.
- 2.2: five tracked files: 0 added, 355 deleted (314/9/9/8/15). Extra: untracked `gui2/data/pass1_auto_kva.json` (written by a run at 10:56 today, 106 words, 105 with the key) also stripped; round trip was byte-identical. `rg -c family_compound gui2/data/pass1_auto_*.json` finds nothing.
- 3.1: remaining hits are the pop line, the new tests, and the ALL / ROOT / COMPOUND / WORD lists in `gui2/dpd_fields_lists.py` (not Pass1 lists).
- 3.2: `just typecheck` 0 errors; gui2 tests 710 passed.
- Side effect: wrote a placeholder `plan.md` in `kamma/threads/20261105_contrib_audio_preview/` (owner's choice) to clear the spec-gate hook.

