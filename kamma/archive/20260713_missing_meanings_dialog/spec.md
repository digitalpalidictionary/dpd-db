# Spec: missing words dialog + "eg" queue in gui2

## GitHub issue
(none provided)

## Origin
Spun off from `kamma/threads/20260713_scripts_triage` while triaging
`scripts/find/missing_meanings.py`. Refined 2026-07-14 with the user's target workflow: use the
last example/commentary of every saved word to continuously discover and add missing dictionary
words.

## Decisions taken on stated defaults (user was AFK — confirm at Task 1)
1. **Criteria = level 3**: flag words absent from the dictionary, plus existing headwords lacking
   `meaning_1` OR lacking `example_1`. Absence of `example_2` alone does not flag a word.
2. **Trigger = every successful save** in `_click_add_to_db` (both the update branch and the
   add-new-word branch).
3. ~~Ignore is persistent~~ **REVERSED 2026-07-14 after testing**: no ignore list at all.
   "Missing" is a property of the word, but skipping is a per-sentence decision — a word skipped
   in one sentence should reappear when found in a better one. Unticked = simply not added this
   time. A manually curated ignore list may come later if noise proves real (deliberately
   deferred — premature optimization).
4. **"eg" button is two-mode**: existing headwords load for editing (like the X button), unknown
   words open a prefilled new-word form (like the New button).

## Overview
After every successful save in `gui2/pass2_add_view.py::_click_add_to_db` (the webapp already
opens via `request_dpd_server`), scan the saved word's `example_1`, `example_2` and `commentary`
with `find_missing_meanings()` and show a dialog of missing words, grouped under the sentence
they came from. Each word is selectable text (for GoldenDict lookup) and tickable. Ticked words
go into a new persistent "eg" queue; unticked words are simply not added this time. A new
**"Eg"** button (placed after P2A and New) pulls the next queued word into the form for
processing.

## What it should do

### 1. Scan on save
- Gated by a `config.ini` setting `[gui2] missing_words_dialog = yes|no` (read via
  `config_read`; anything other than "yes" disables the dialog — sometimes it's useful,
  sometimes a distraction). The Eg button and queue keep working regardless; the toggle only
  controls the dialog. Config is read at app start (configger loads at import), so toggling
  needs a gui2 restart.
- In `_click_add_to_db`, after `committed` is True (both branches), run
  `find_missing_meanings(db_session, text, level=3)` **separately per field** —
  `example_1`, `example_2`, `commentary` — so each missing word's sentence context is known.
- Deduplicate across fields (first occurrence wins) and drop words already in the eg queue or
  equal to the just-saved word's own lemma.
- Strip `<b>`/`</b>` tags from the example/commentary text stored in the queue prefills.
- If nothing remains, no dialog appears — the save flow is unchanged (silent common case).

### 2. Dialog
- `ft.AlertDialog` following the `delete_alert` pattern in `pass2_add_view.py` (~line 881).
- Words are grouped by the source sentence they came from: each section shows the full
  example/commentary text (selectable, grey), followed by that sentence's missing words in
  order of appearance in the text (existing headwords are lemma_1 values whose inflected form
  is in the text — appearance position is matched on a progressively shortened stem,
  unmatched words last). Sections in field order: example_1, example_2, commentary.
- One row per missing word: an **unchecked-by-default** `ft.Checkbox` + the word as plain
  **selectable text** (no button/click action) — the user selects the word and looks it up in
  GoldenDict themselves.
- Actions:
  - **"Add ticked"** — ticked words are written to the eg queue with their sentence context;
    unticked words are simply not added (no memory of the decision).
  - **"Close"** — dismiss with no side effects.

### 3. eg queue storage (new module `gui2/pass2_eg_manager.py`)
- Follow the `Pass2NewWordManager` pattern (`gui2/pass2_pre_new_word_manager.py`): JSON dict in
  `gui2/data/pass2_eg_words.json`, atomic save, `get_next()` pops the first entry.
- Each entry stores the prefill dict + a comment (`f"eg: found in {lemma_1}"`) so origin is
  traceable. Prefill mapping by origin field of the *saved* word:
  - found in `example_1` → `{source_1, sutta_1, example_1}` from the saved word's `_1` fields
  - found in `example_2` → `{source_1, sutta_1, example_1}` from the saved word's `_2` fields
  - found in `commentary` → `{example_1: <commentary text>}` (changed 2026-07-14: the goal is
    to get everything into example_1; commentary has no source/sutta columns so those stay
    empty)
- Bold tags are stripped from all prefill text.
- New path added to `gui2/paths.py`. (An ignore list existed briefly and was removed — see
  decision 3 above.)

### 4. "eg" button
- New `ft.ElevatedButton("Eg", ...)` placed immediately after `self._new_word_button` in the
  top row of
  `pass2_add_view.py`, with a remaining-count tooltip like its siblings.
- On click, pop the next queue entry, then **two-mode load**:
  - If the word matches an existing headword (query `DpdHeadword` by `lemma_1`, falling back to
    `lookup` → headword id resolution): load it for editing exactly like `_click_x_button` does
    (`clear_all_fields`, set `self.headword`/`headword_original`, `update_db_fields`,
    `add_headword_to_examples_and_commentary`), then prefill the stored example context into the
    empty `_2`/commentary fields via `update_add_fields` where sensible.
  - Otherwise: new-word mode like `_click_load_new_word` — `clear_all_fields` +
    `update_add_fields(prefill_dict)`.
- Queue empty → message "No more eg words".

## Reused infrastructure (do not reinvent)
- `scripts/find/missing_meanings.py::find_missing_meanings` — import as-is; do not copy or
  modify. (Note: it `print`s its result — acceptable console noise, do not edit the script.)
- `tools/fast_api_utils.py::request_dpd_server` — opens a query in the local webapp.
- `Pass2NewWordManager` as the pattern for the new eg manager (not reused directly — the eg
  queue is deliberately separate from the organic "New" queue).
- Dialog pattern: `delete_alert` in `pass2_add_view.py`.

## Assumptions & uncertainties
- The four defaults listed at the top — confirm with the user before/at Task 1.
- Exact two-mode resolution for existing words: lemma match may be ambiguous with homonyms
  (`kata 1`, `kata 2`). If a flagged lemma_1 matches exactly one headword, load it; if multiple
  or none, fall back to new-word mode with the word placed in `lemma_1` so the user decides.
- Whether prefilling `_2` fields on an *existing* loaded headword is wanted, or just load the
  headword bare — minor; decide during implementation, easy to adjust.

## Constraints
- Modern type hints, no `sys.path` hacks, `Path` for file paths.
- Never mutate ORM objects as a side effect of the scan.
- Files touched: `gui2/pass2_add_view.py`, new `gui2/pass2_eg_manager.py`, `gui2/paths.py`
  (2 new paths). Nothing else.
- gui2 is pyright-excluded but NOT ruff-excluded — all touched files must pass
  `ruff check` + `ruff format`.

## How we'll know it's done
- Manual verification in the running gui2 app: save a word whose examples/commentary contain a
  missing word → dialog appears; clicking the word opens it in the webapp; "Add ✓ / Ignore ✗"
  writes ticked words to `pass2_eg_words.json`, unticked words are untouched; "Eg" button loads
  an existing headword in edit mode and an unknown word in new-word mode with the example
  prefilled.
- Saving a word with no missing words shows no dialog.
- `uv run ruff check` + `ruff format` clean on all touched files.

## What's not included
- No changes to `find_missing_meanings()` itself.
- No bulk/background scan across the whole db — per-word, at save time only.
- No changes to the existing "New" queue or `_click_load_new_word`.
