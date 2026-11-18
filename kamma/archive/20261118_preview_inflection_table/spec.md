# Spec: preview builds its button content

## Overview

After a word is added or edited in gui2 (Pass1 add, Pass2 add), a preview page opens
before the word is saved. The page is the webapp's headword HTML, rendered from a
transient copy of the word (`gui2/preview.py`, `render_preview`). Some buttons on that
page show content that the db build normally generates later, or that a web server
normally serves. For an unsaved word that content is empty, stale or dead. This thread
fixes three buttons and one related list bug.

Related placeholder thread: `kamma/threads/20261105_contrib_audio_preview` (issue #215,
audio in the preview, desktop only). This thread does that audio work. Finalize should
retire that placeholder.

## Decisions (owner, 2026-11-18)

- **Inflection table:** build it from stem + pattern.
- **Frequency:** the counts need the Go tool, so the preview cannot build them. The
  frequency box says the frequency is not built yet, instead of "no matches".
- **Audio:** the play button must work when the audio is already in the audio database.
- **Word list bug:** fix `tools/all_tipitaka_words.py` (reads the SYA list twice, never the
  SuttaCentral list).
- **Family buttons** (root, word, compound, idiom, set): not included. Stay as the db has them.

## What it should do

### 1. Inflection table

- When the previewed word has a `pattern`, build its table from `stem` + `pattern` + the
  `inflection_templates` row, and set it as the copy's `inflections_html`.
- Same HTML the db build writes (`InflectionsManager.generate_inflection_table` in
  `db/inflections/generate_inflection_tables.py`): heading line, grid, grey cells for forms
  found in no corpus.
- It shows on the declension button (pos in `DECLENSIONS`) or the conjugation button (pos in
  `CONJUGATIONS`). Both read `d.i.inflections_html`. Button logic is not changed.
- A new word shows a table instead of an empty box. An edited word whose stem or pattern
  changed shows the new table, not the stale one from the form.

### 2. Frequency box

- Template (`exporter/webapp/templates/dpd_headword.html`, frequency block): when
  `freq_html` is empty it says "There are no matches of X in any texts".
- In the preview, when the copy's `freq_html` is empty, set it to a short note: frequency
  is calculated when the dictionary is next built.
- An edited word that already carries a stored `freq_html` keeps it. A word that is saved
  in the db with an empty `freq_html` (4,878 of them: counted, no matches) also keeps the
  webapp's own "no matches" text. The note is for words not in the db yet only.
- Wording of the note: to be settled in the plan (one short sentence, no promise about
  timing beyond "next build").

### 3. Audio

- Today the preview hides the play button (`.dpd-button.play{display:none}`) because the
  webapp's script asks the server for `/audio/<word>?gender=<g>`, and a saved preview file
  has no server.
- Desktop gui2: if the word's `lemma_clean` is in the audio index
  (`tools/cache_load.load_audio_dict`), read each available recording with
  `audio.db.db_helpers.get_audio_record` (male1, male2, female1), embed them in the page as
  base64 data, and add a small script that makes `new Audio('/audio/...')` play the embedded
  data. The webapp's `dpd.js` is not edited.
- The script must also answer the generic keys the webapp uses: `male`, `female`, and the
  voice-specific buttons in the grammar table (`male1`, `male2`, `female1`). Fallback rules
  match `get_audio_record` (`female` = female1 else male1; anything else = male1 else female1).
- Words with no recording keep the button hidden.
- If the audio index or db file is missing, the button stays hidden and nothing fails. The
  db file is checked with `exists()` first, because opening a missing sqlite file creates an
  empty one. The contributor server downloads the index but not the db, and its users add
  new words (Pass1), so it skips audio this way (owner decision, 2026-11-18: no special
  server check).
- A new word has audio only when its `lemma_clean` already exists in the audio index.

### 4. Word list fix

- `make_all_tipitaka_word_set` in `tools/all_tipitaka_words.py` opens `sya_wordlist` for
  the variable `sc_wordlist`. It must open `pth.sc_wordlist`.
- Measured 2026-11-18: `sc_wordlist.json` has 169,419 words. 8,067 of them are in none of
  the CST, BJT and SYA lists. The combined set grows from 1,135,694 to 1,143,761 words. Of 500
  sampled inflection tables, 26 get different grey cells.
- Two build scripts use the set: the inflection tables (grey cells) and
  `db/inflections/inflections_to_headwords.py` (which inflections map to headwords, and the
  TPR i2h file). Both change at the next db rebuild: fewer grey cells, more i2h entries.
  The fix does not rebuild the db.

## Current behaviour (read from source)

- `render_preview` copies every column the word object carries (`_copy_of`), then renders
  the webapp template. `inflections_html` and `freq_html` are only what the caller supplied.
- New word: both are `""`. Edited word: both are form fields (`gui2/dpd_fields_lists.py`),
  so they hold the old db values.
- The play button shows when `lemma_clean` is in the audio index (`needs_audio_button`).
  The audio db is `audio/db/dpd_audio.db` (about 1.2 GB; the index is a 1.6 MB TSV).
- Existing test `test_page_is_dark_opens_grammar_and_hides_audio` asserts the hide rule is
  in the page. It must change: the rule stays only for words without embedded audio.

## Assumptions & uncertainties

Verified by reading source this session: `render_preview`, `_copy_of`, both callers, the
template's button and content blocks, the generator, `InflectionTemplates` (key `pattern`),
`dpd.js` audio code, the server's `/audio/` route, `get_audio_record` and its gender
fallback, `load_audio_dict`, the word-list bug and both consumers.

Not verified, to be checked in the plan:

- That an edited word in the real gui2 flow arrives with the old `inflections_html` and
  `freq_html` (the test helper fills every column; the real form path is not traced).
- Load time of the four word-list files per preview (spec says no cache; revisit above 3 s).
- Whether the contributor server has the word-list files. They are git-ignored generated
  files. If missing, the table shows with no grey marking and the preview still works.
- Size of one word's embedded audio and the time to read it from the 1.2 GB db.
- That the Flet web client lets a page opened from `gui2/assets/preview/` play data-URI audio.
  Desktop is the owner's stated target; a browser autoplay block would show as a silent click.

## Constraints

- The db build output of the table builder must not change in Phase 1 (strict preservation).
  Only the word-list fix changes build output, and that is intended.
- No `.env` or `.ini` edits. Only the transient copy changes; nothing is added to the session.
- A missing audio db is skipped quietly and never created.
- Touch a file = own its lint: `ruff check`, `ruff format`, `pyright` (`--project /dev/null`
  for `gui2/` and `tests/`) clean on every file touched; `just typecheck` before finishing.
- Never run git commands. Never run the db build.

## How we'll know it's done

- Tests: new word shows the table; edited pattern shows the new table; empty `freq_html`
  shows the note and a stored one is kept; a word with audio carries embedded audio and a
  visible play button; a word without audio keeps the button hidden; a missing audio db is
  skipped, never read and never created; the word set contains SuttaCentral-only words.
- Equivalence: over at least 300 real words, the extracted builder's output equals the stored
  `inflections_html` (run before the word-list fix).
- Revert check: with each change reverted, its tests fail (counts reported).
- One real gui2 run by the owner: preview a word that has audio, press play, hear it; press
  the declension or conjugation button and see the table; press frequency and see the note.

## What's not included

- Frequency counts. Family tables. Sutta info (needs a saved row). Example and grammar
  (already built from the form fields). Changing which buttons show.
- Rebuilding the db after the word-list fix.
- Audio on the contributor server.
