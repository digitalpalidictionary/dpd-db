# Pass1Add: AI suggestions go to the `_add` column, like Pass2Add

## Overview

Pass1Add (gui2 tab) loads each word that Pass1Auto has processed. Today it
writes the AI's answer straight into the editable main fields. The editor must
then delete or rewrite every guess they do not want.

Pass2Add already solves this. Each field row is
`label | main field | ← transfer button | _add field`. Suggestions land in the
read-only grey `_add` field. The editor clicks ← to copy one across, or ignores
it. This thread gives Pass1Add the same column and the same load behaviour, so
AI output is only ever a suggestion.

## Current behaviour (verified by reading the code, 2026-10-11)

- `gui2/pass1_add_view.py::_build_middle_section` builds `DpdFields` and calls
  `self.dpd_fields.add_to_ui(middle_section, visible_fields=PASS1_FIELDS)`
  with no `include_add_fields`, so the `_add` column and ← buttons are not
  mounted.
- `gui2/pass1_add_controller.py::load_into_gui` loops over `self.sentence_data`
  (one entry of `gui2/data/pass1_auto_<book>.json`) and sets
  `self.ui.dpd_fields.fields[field].value = data` for every key that is a field.
- That JSON entry is written by `gui2/pass1_auto_controller.py::update_auto_processed`.
  It holds the AI's JSON (`lemma_1`, `lemma_2`, `pos`, `grammar`, `meaning_2`,
  `root_key`, `root_sign`, `root_base`, `family_root`, `family_compound`,
  `construction`, `stem`, `pattern`, `comment` — the comment is prefixed
  `[provider: model]`) plus up to four keys copied from the source text, not
  the AI: `example_1`, `translation_1`, `example_2`, `translation_2`.
- After a successful save, `make_dpd_headword_and_add_to_db` loads the next
  item and shows `f"{fields['lemma_1'].value} loaded"`.
- `_handle_history_selection` writes a saved headword into the main fields. It
  does not clear anything first.

## Reusable Pass2Add machinery (all in `gui2/dpd_fields.py`, shared by both tabs)

- `DpdFields.__init__` already creates a `<name>_add` `DpdText` for **every**
  field, in both tabs.
- `add_to_ui(..., include_add_fields=True)` mounts the ← button and `_add` field
  on each row. It works together with `visible_fields`.
- `update_add_fields(data)` fills `_add` fields, enables the ← buttons, and
  colours a suggestion red when it differs from the main field. It ignores
  keys that have no `_add` field.
- `transfer_add_value` copies one `_add` value into its main field.
- `clear_fields(target="add")` empties the `_add` column. Pass2Add's split uses
  it for the same reason this thread does: stale suggestions must not sit next
  to a different word.

Pass2Add's "load new word" (`_click_load_new_word`) is the closest precedent:
a brand-new word, main fields empty, everything offered in `_add`.

## What it should do

1. Pass1Add mounts the `_add` column: `add_to_ui(..., visible_fields=PASS1_FIELDS,
   include_add_fields=True)`.
2. `load_into_gui` splits the loaded entry:
   - The four source-text keys (`example_1`, `translation_1`, `example_2`,
     `translation_2`) still go straight into the main fields. *(User decision
     2026-10-11: they are the real text, not a guess.)*
   - Every other key goes to `dpd_fields.update_add_fields(...)`. The main
     fields stay empty.
3. After a successful save, the "next item loaded" message names the word in
   the text, not `lemma_1`. `lemma_1` is now empty at that point, so the old
   message would read " loaded".
4. Loading a headword from the History dropdown clears the `_add` column first.
   The suggestions belong to the word in the text, not to the history word.
   A stray ← click would otherwise copy them onto the wrong entry.
   It clears them with `update_add_fields({name: ""})`, NOT
   `clear_fields(target="add")`. `clear_fields` also calls `flags.reset()`,
   which would let `stem_blur`, `lemma_2_blur`, and `pos_blur` overwrite the
   saved stem, pattern, and lemma_2. *(Found by CodeRabbit in review.)*
5. The change applies to every user, including server contributors. *(User
   decision 2026-10-11.)*
6. *(Added by the user 2026-10-11, mid-thread.)* The bottom-row button
   "Add to Spelling mistakes" wraps onto two lines at `BUTTON_WIDTH`. Rename it
   "Add to Spelling", matching "Add to Sandhi" and "Add to Variants".
   Label only; the handler is unchanged.
7. *(Added in review.)* "Process Book" clears the form (`clear_all_fields`)
   before it loads the first word. Otherwise stale `_add` values from the
   previous word could stay beside the new one.

## Side effects checked

- **Saving ignores `_add` fields.** The save path filters on
  `hasattr(DpdHeadword, name)`. `get_current_values` → `make_dpd_headword_from_dict`
  (used by Test and the phonetic helper) does the same. `db/models.py` has no
  attribute ending in `_add`.
- **Clear All, Pass, Delete, save-then-next, and (after item 7) Process Book** all rebuild the middle section
  (`clear_all_fields` → `_build_middle_section`). That makes a new `DpdFields`,
  so `_add` values and ← button states reset with no extra code.
- **Clone** only fills empty main fields from `PASS1_FIELDS`, minus `id` and
  examples. It never reads or writes `_add`. Unchanged.
- **Spelling gate** checks the main `meaning_2` and `meaning_lit` only. An
  unaccepted suggestion is never checked or saved. This is the intended effect.
- **Comment.** The AI comment now lands in `comment_add`. It is saved only if the
  editor copies it across. Intended.
- **Rule-based helpers** (`pos_blur` → `lemma_2`, `construction_focus`,
  `family_compound_focus`, `stem_blur`, etc.) fire only on real focus and blur
  events. A ← copy is a programmatic set and fires none of them, the same as
  the old direct load. Some helpers fill a field only when it is empty. Before,
  the AI's value stopped them. Now they will fill an empty field when the
  editor tabs into it, exactly as in Pass2Add's new-word flow. A ← click still
  overwrites whatever a helper wrote.
- **Helpers that already write `_add`** (`compound_type_add`, `phonetic_add`,
  `synonym_add`, `var_phonetic_add`) keep working. Their rows are not in
  `PASS1_FIELDS`, so they stay hidden. The comment at
  `gui2/dpd_fields.py:1598` ("Pass1Add never mounts the `_add` shadow fields")
  becomes stale. The `is_mounted` guard under it stays, because hidden rows
  can still be unmounted.
- **Pass1Auto** is not touched. It still writes the same JSON.
- **Tab order** now passes through the ← buttons, as in Pass2Add.

## Assumptions & uncertainties

- Assumed: the Pass2Add row layout (main field 700 px wide + 500 px `_add`)
  fits the screens people use for Pass1Add. Pass2Add uses it today on desktop.
  The web-server contributors' screen widths were not checked.
- Assumed: no other code writes into Pass1Add's main fields during load. A
  repo-wide `rg --hidden "pass1_add|Pass1Add"` found only the view, the
  controller, type hints in the `dpd_fields_*` modules, and kamma/conductor docs.
- Open thread overlap: `kamma/threads/20261007_preview_before_save/` (not
  started) will edit `make_dpd_headword_and_add_to_db` in
  `gui2/pass1_add_controller.py`. This thread touches only the post-save
  message line in that function. Whichever thread lands second must re-read it.

## Constraints

- Reuse the shared `DpdFields` methods. Do not copy Pass2Add code into Pass1Add.
- No change to `gui2/dpd_fields.py` behaviour. Only the stale comment is updated.
- Concurrent threads share the tree: stage by explicit file list, and never use
  whole-tree git commands.
- Every touched file must pass `ruff check`, `ruff format`, and `pyright`.

## How we'll know it's done

1. A new unit test proves `load_into_gui` puts AI keys in `_add` only and the
   four source-text keys in the main fields. It fails when the split is reverted.
2. Live run: Pass1Add shows the ← column. A loaded word has empty main fields
   (examples filled), grey/red suggestions, and working ← buttons.
3. Live run: save a word with only some suggestions copied. The db row holds
   only the copied values. The message names the next word.
4. Live run: History load clears the suggestions. Clear All, Pass, and Delete
   still work.
5. `just typecheck` and the existing `tests/gui2/` suite pass.

## What's not included

- A "copy all suggestions" button. Pass2Add has none. Add one later if the
  per-field clicks are too slow.
- Changes to Pass1Auto, its prompt, or its JSON format.
- Logging suggested-vs-final values, as Pass2Add's save does for `pass2_add`.
- Pre-filling `lemma_1` from the word in the text.
