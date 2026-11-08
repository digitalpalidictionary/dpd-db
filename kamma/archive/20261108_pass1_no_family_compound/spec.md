# Spec: remove family_compound from Pass1 Auto and Pass1 Add

GitHub issue: #215 (contributor web server) — assumed, see Assumptions.

## Overview

Pass1 Auto asks the AI for a `family_compound` value for every new word, saves it into
`gui2/data/pass1_auto_<book>.json`, and Pass1 Add shows it as a suggestion beside an editable
`family_compound` field. This thread removes the field from that whole chain.

Why:
1. It is too hard for beginner contributors to fill in correctly.
2. It has no effect on Pass1 entries. `db/families/family_compound.py` (line 76-80) only puts a
   headword into a compound family when it has `meaning_1`. Pass1 entries have only `meaning_2`,
   so their `family_compound` never shows in any entry. (Verified by reading the code.)

## The chain today (verified by reading the code, 2026-11-08)

1. **Prompt** — `gui2/pass1_context.py`
   - `ANSWER_KEYS` (line 30) lists `family_compound`. The JSON skeleton in the prompt is built
     from it, so the AI is told to return the key.
   - `related_entry_dict()` (line 186) puts each related headword's `family_compound` into the
     related entries shown to the AI.
   - `_EXAMPLE_ANSWER` (line 373) has `"family_compound": "loka nāyaka"`.
   - `_FIELD_RULES` has a `## family_compound` section (lines 427-432).
   - `build_old_prompt()` (lines 232-355) and `SYSTEM_PROMPT_OLD` (line 37) are a frozen copy of
     the pre-2026-11 prompt. gui2 never calls them. Only one unit test does
     (`tests/gui2/test_pass1_context.py::test_old_prompt_sentence_and_related_lines`), plus the
     archived scripts in `kamma/archive/20261104_pass1_auto_prompt/artifacts/eval/`.
2. **Controller** — `gui2/pass1_auto_controller.py::update_auto_processed()` parses the AI's
   JSON and saves every key it got, as is, via `add_word()` into the book's JSON file. It does
   not filter keys.
3. **Files** — five git-tracked files hold drafts. Every word has the key:

   | file | words | with key | non-empty |
   |---|---|---|---|
   | pass1_auto_ap.json | 314 | 314 | 171 |
   | pass1_auto_bv.json | 9 | 9 | 3 |
   | pass1_auto_cp.json | 9 | 9 | 7 |
   | pass1_auto_pv.json | 8 | 8 | 6 |
   | pass1_auto_vv.json | 15 | 15 | 12 |

   Added 2026-11-08, found during the work: `pass1_auto_kva.json` is NOT tracked by git. A Pass1
   Auto run wrote it at 10:56 that day (106 words, 105 with the key). It was stripped too, so the
   owner must add it by explicit path when committing it.

   They are written by `Pass1FileManager` with `json.dump(..., ensure_ascii=False, indent=4)`,
   no trailing newline. A load-then-dump round trip of `pass1_auto_bv.json` is byte-identical.
   `gui2/data/pass1_auto_retired/` (gitignored backups) and `pass1_auto_text.json` (gitignored,
   not present now) are not touched.
4. **Screen** — `gui2/pass1_add_view.py` shows the fields in `PASS1_FIELDS`
   (`gui2/dpd_fields_lists.py` line 336 has `family_compound`). `DpdFields.add_to_ui()` builds
   every field and only hides those not in the list. `Pass1AddController.load_into_gui()` puts
   each AI key into its `<field>_add` box. The Clone button copies only `PASS1_FIELDS` fields.
   On save, `make_dpd_headword_and_add_to_db()` collects every field that is a `DpdHeadword`
   attribute, hidden or not.
5. **Other users of `PASS1_FIELDS`**
   - `gui2/pass2_add_view.py` line 734: Pass2 Add's "pass1" filter button.
   - `scripts/find/missing_pr_verbs.py` line 59: builds `QUEUE_FIELDS`. That script already
     leaves `family_compound` empty and drops empty values, so its output does not change.

## What it should do

1. The Pass1 Auto prompt no longer mentions `family_compound` anywhere: not in the answer keys,
   the example, the field rules, or the related entries.
2. If an AI still returns a `family_compound` key, the controller drops it before saving, so no
   new JSON draft holds it.
3. The old frozen prompt (`build_old_prompt`, `SYSTEM_PROMPT_OLD`) and its one unit test are
   deleted. The module docstring stops naming an old prompt builder.
4. The `family_compound` key is removed from every word in the five tracked
   `pass1_auto_*.json` files. Nothing else in those files changes.
5. `family_compound` is removed from `PASS1_FIELDS`. The field row is hidden in Pass1 Add and in
   Pass2 Add's "pass1" filter (owner's choice, 2026-11-08). All other Pass2 filters still show it.

## Assumptions & uncertainties

- The hidden `family_compound` field still exists in Pass1 Add. It stays empty for new words, so
  they save with `family_compound = ""`. A word loaded from history fills every field from the
  db, hidden ones too, so re-saving keeps its existing `family_compound`. (Verified in
  `DpdFields.update_db_fields`.)
- Contributor additions (`gui2/data/additions_<user>.json`) keep any `family_compound` already
  in them. This thread does not touch them.
- The rewritten JSON files reach the contributor server through git, as today. The server's
  `pass1_auto_removed_<user>.json` lists hold word names only and are unaffected.
- The data rewrite must run with gui2 closed and no Pass1 Auto run going, or a running gui2
  can write the old content back.
- Issue #215 is a guess, from the contributor reason. The owner can change it.
- The archived eval scripts in `kamma/archive/20261104_pass1_auto_prompt/` will no longer run
  after the old prompt is deleted. Owner accepted this.

## Constraints

- Never `git stash` / `restore` / `checkout --` (shared tree, other threads).
- Lint every touched Python file: `ruff check`, `ruff format`, and
  `uv run pyright --project /dev/null <file>` for files under `gui2/` and `tests/`.
- Rewrite the JSON files with the same `json.dump` settings as `Pass1FileManager`, so the diff
  is only the removed lines.
- The rewrite script is a throwaway in the scratchpad, not committed.

## How we'll know it's done

- `rg -n family_compound gui2/pass1_context.py gui2/pass1_auto_controller.py
  gui2/pass1_add_controller.py gui2/pass1_add_view.py` returns only the controller's drop line.
- `rg -c family_compound gui2/data/pass1_auto_*.json` finds no match.
- `git diff --stat gui2/data/pass1_auto_*.json` shows only deletions: 355 lines.
- A test shows an AI answer with `family_compound` is saved without it, and fails if the drop
  line is removed.
- `uv run pytest tests/gui2/test_pass1_context.py tests/gui2/test_pass1_auto_controller.py
  tests/gui2/test_pass1_add_controller.py tests/gui2/test_pass1_add_view.py` passes.
- Live: Pass1 Add shows no `family_compound` row for a word from a book file.

## What's not included

- `family_compound` in Pass2 Add (except its "pass1" filter), Pass2 Auto, and the rest of gui2.
- Contributor addition files.
- `family_word` and the other family fields.
- The retired backups in `gui2/data/pass1_auto_retired/`.
