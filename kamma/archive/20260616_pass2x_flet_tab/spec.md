# Spec: pass2x_flet_tab (in-commentary GUI, stage 2)

## GitHub issue
#162 — gui2 improvements (umbrella; do NOT close).

## Context
Stage 1 (archived `kamma/archive/20260616_pass2x_in_commentary/`) built and proved the
read-only data pipeline in `gui2/pass2x/in_commentary_tui.py`: harvest words from
`DpdHeadword.commentary` → keep those that are an inflected form of an **incomplete**
headword (`not (meaning_1 and source_1)`) → pull Pāḷi+English example paragraphs from the
Tipiṭaka translations db, word bolded. **The data is final.** This thread puts that data
behind a real Flet GUI.

## Goal (user-approved scope "A" — full mirror)
A new **Pass2x** tab in gui2, between **Pass2Pre** and **Pass2Auto**, whose first button is
**"in commentary"**. Clicking it loads the stage-1 pipeline and walks the user through each
candidate word → its incomplete headword(s) → a **selectable** list of example sentences
(Pāḷi bolded + English), offering **Yes / No / Pass**. A "yes" persists in the exact
`matched` shape that **Pass2Auto already consumes**, so the existing Pass2Auto (AI or NO-AI)
completes the headword. Nothing here writes to `dpd.db` directly — it only writes the
matched/unmatched JSON; Pass2Auto remains the db-writing path.

## Design decisions (locked)
1. **Data source = stage-1 pipeline, unchanged.** The controller imports
   `harvest_commentary_words`, `build_inflection_map`, `find_examples_for_candidates`,
   `Example`, `CommentarySource` from `gui2/pass2x/in_commentary_tui.py`. No refactor of
   stage 1 (data is final); the TUI keeps working. Word→headwords comes from the
   inflection map (NOT `db.get_headwords`/`Lookup`), preserving stage-1 semantics.
2. **Persistence reuses `Pass2PreFileManager("in_commentary", paths)`.** This writes
   `gui2/data/pass2_pre_in_commentary.json` with the same `matched` / `unmatched` /
   `processed` structure Pass2Pre uses. No new file-manager class — the shared format IS
   the wiring. "Yes" → `update_matched(word, headword_id, sentence)`; "No" →
   `update_unmatched(word, headword_id)`.
3. **`sentence` = `CstSourceSuttaExample(source, sutta, example)`** (a 3-field namedtuple),
   built from the selected `Example` as `(ex.source, ex.paranum, ex.pali_raw)`. Pass2Auto's
   `_add_sentence_to_response` maps `[0]→source_1`, `[1]→sutta_1`, `[2]→example_1`.
4. **Pass2Auto consumes it via the existing book machinery.** Add `"in_commentary"` to
   `Pass2AutoController.sc_books_list` so it appears in the Pass2Auto book dropdown, and
   guard the (dead, assigned-but-never-read) `self._cst_books = self._sc_books[book].cst_books`
   line so the non-sutta book key doesn't KeyError. No other Pass2Auto logic changes.
5. **Example sentences are sourced just-in-time, per word — uncapped — with a keyword
   filter.** (Revised 2026-06-16 after review: the original bulk pre-scan of all ~18k
   candidates with a `EXAMPLE_CAP=5` cap was wrong — a session only processes ~20 words, so
   pre-scanning everything is wasteful and the cap was never requested.) `load_in_commentary`
   now only harvests words + builds the inflection map (no translations scan); each word's
   examples are found when it becomes current via a new `find_examples_for_word(path, word)`
   in `in_commentary_tui.py` (SQL `LIKE` pre-filter + Python whole-word verify, **no cap**),
   accepting a ~1–2 s per-word delay. The view filters the (now possibly many) translation
   examples by a `SearchBar` keyword and paginates at 50 (More/Less), mirroring Pass2Pre.
6. **The commentary (example #0) is shown and copyable but never selectable** — it has no
   `Radio` and is excluded from the keyword filter; it is always displayed for context.
7. **All new files live in `gui2/pass2x/`** (plus the additive `find_examples_for_word` in the
   existing `in_commentary_tui.py`).

## Files
- **NEW** `gui2/pass2x/in_commentary_controller.py` — `Pass2xInCommentaryController`,
  mirrors `Pass2PreController` (load → walk words → walk headwords → yes/no/pass).
- **NEW** `gui2/pass2x/in_commentary_view.py` — `Pass2xInCommentaryView(ft.Column)`, the tab
  content, mirrors `Pass2PreProcessView` (word/headword fields, Yes/No/Pass + exceptions
  field, message + counter, `SearchBar` keyword filter, paginated selectable example
  `RadioGroup`). Hosts the **"in commentary"** button (the first of the tab's eventual set).
- **EDIT** `gui2/pass2x/in_commentary_tui.py` — additive `find_examples_for_word(path, word)`
  for the per-word JIT search (the existing bulk function and TUI are untouched).
- **EDIT** `gui2/main.py` — import + instantiate the view; insert `ft.Tab(text="Pass2x", …)`
  between Pass2Pre and Pass2Auto; fix the `_get_current_lemma` tab-index map (Pass2Add
  shifts 6→7).
- **EDIT** `gui2/pass2_auto_control.py` — add `"in_commentary"` to `sc_books_list`; guard the
  two dead `_cst_books` assignments.

## Behaviour
- **In commentary button:** show "loading…", harvest commentary words + build the inflection
  map (no translations scan), build `resolved` (word→headwords) and the work queue of words
  not already in `matched`/`unmatched`/`processed`; load the first word/headword. Re-click
  reloads.
- **Per word (just-in-time):** when a word becomes current, search the translations DB for
  **all** its example paragraphs (`find_examples_for_word`, ~1–2 s, shows "searching
  examples…"); these are reused across that word's headwords.
- **Per headword:** display `lemma_1`, `pos`, `meaning_combo [construction_summary]`; render
  example #0 (the commentary, copyable but not selectable) followed by the keyword-filtered,
  paginated translation examples as selectable radios; open the headword in GoldenDict.
- **Yes:** persist matched(word, current headword id, selected example as CstSourceSuttaExample),
  advance to next headword.
- **No:** persist unmatched(word, current headword id), advance.
- **Pass:** advance without persisting.
- **Exceptions field:** add the typed word (or current word if blank) to
  `InCommentaryExceptions`, drop it from the queue, advance to the next word.
- When a word's headwords are exhausted: increment `daily_log["pass2x"]`, next word. When the
  queue empties: "No more words to process."

## Out of scope (deferred, do not implement)
- Deconstructor/compound recursion and variant/spelling exclusions (still deferred from
  stage 1).
- Any change to how Pass2Auto AI-processes a headword.
- More Pass2x buttons beyond "in commentary".
- Direct db writes from Pass2x.
- New automated tests for the Flet UI (GUI-manual verification by the user, who runs `/gui2`).

## How we'll know it's done
- gui2 launches with a **Pass2x** tab between Pass2Pre and Pass2Auto.
- "in commentary" loads candidates and shows word → headword(s) → bolded Pāḷi + English
  selectable examples.
- Yes/No/Pass advance correctly; Yes writes `gui2/data/pass2_pre_in_commentary.json` in the
  matched shape.
- Selecting `in_commentary` in the **Pass2Auto** book dropdown and running NO-AI/AI processes
  those matched entries with no KeyError.
- `ruff check` + `ruff format` clean on every touched file.
