# Plan: pass2x_flet_tab

Spec: `spec.md`. Scope "A" (full mirror) — user-approved.

## Phase 5 — Per-word JIT + uncapped + filter (revision, 2026-06-16)
- [x] T6. Replace the bulk pre-scan with just-in-time per-word example search:
  add `find_examples_for_word(path, word)` (uncapped, `LIKE` + verify) to `in_commentary_tui.py`;
  rework the controller (`word_queue` + `current_examples`, examples found in `load_next_word`);
  add a `SearchBar` keyword filter + 50-item pagination to the view; make the commentary
  (example #0) shown/copyable but unselectable and filter-excluded.
  → verify: `ruff check` + `pyright` on the three files (clean).

## Phase 1 — Controller (data + flow)
- [x] T1. `gui2/pass2x/in_commentary_controller.py` — `Pass2xInCommentaryController`:
  imports stage-1 pipeline from `in_commentary_tui`; reuses
  `Pass2PreFileManager("in_commentary", toolkit.paths)`; `load_in_commentary()` builds
  `resolved` + `examples_by_word` + work queue; `load_next_word()` / `load_next_headword()`
  mirror Pass2Pre; counter + GoldenDict.
  → verify: `ruff check gui2/pass2x/in_commentary_controller.py`.

## Phase 2 — View (the tab)
- [x] T2. `gui2/pass2x/in_commentary_view.py` — `Pass2xInCommentaryView(ft.Column)`:
  "in commentary" button, word/headword fields, Yes/No/Pass + exceptions field, message +
  counter, selectable example `RadioGroup` (≤6, word bolded via `highlight_word_in_sentence`,
  ṁ→ṃ normalised). Yes builds `CstSourceSuttaExample(ex.source, ex.paranum, ex.pali_raw)`.
  → verify: `ruff check gui2/pass2x/in_commentary_view.py`.

## Phase 3 — Wire into the app
- [x] T3. `gui2/main.py` — import + instantiate view; insert `ft.Tab(text="Pass2x")` between
  Pass2Pre and Pass2Auto; fix `_get_current_lemma` map (Pass2Add 6→7).
  → verify: `ruff check gui2/main.py`.
- [x] T4. `gui2/pass2_auto_control.py` — add `"in_commentary"` to `sc_books_list`; guard the
  two dead `_cst_books` assignments against the non-sutta key.
  → verify: `ruff check gui2/pass2_auto_control.py`.

## Phase 4 — Gate
- [x] T5. `ruff check --fix` + `ruff format` + `pyright` on all touched files; fix every
  reported error (own the whole file). Report to user for GUI-manual verification via `/gui2`.

## Notes / deviations
- Persistence reuses `Pass2PreFileManager("in_commentary")` rather than a new
  `gui2/pass2x/` file-manager class — the shared on-disk format IS the Pass2Auto wiring,
  so a parallel class would add nothing. (Noted/approved in spec decision 2.)
- No `pytest`/import-execution run: project rule forbids running scripts unasked; GUI files
  have no unit tests. Verification = ruff clean + ruff format + pyright clean; GUI behaviour
  is the user's manual check via `/gui2`.
- REVISION (2026-06-16, user review): dropped the bulk pre-scan + `EXAMPLE_CAP=5` (never
  requested). Examples now found just-in-time per word, uncapped, and keyword-filterable.
  Stage-1 `EXAMPLE_CAP`/`find_examples_for_candidates` and the TUI are left intact (additive
  `find_examples_for_word` only). See spec decisions 5–6.
- BUGFIX (2026-06-16, runtime): `daily_log.increment("pass2x")` raised — `pass2x` was not in
  `daily_log.py`'s key whitelist, freezing the UI after "Yes". Registered `pass2x` as a valid
  key (+ default dicts + appbar counts string).
- ADDITION (2026-06-16, user request): machine table names (`e0104n_att`) are now translated
  via `tools/cst_book_translator.py` — `Example.source` holds the DPD book code (e.g. `VISMa`,
  saved into `source_1` so it's findable in Pass2Add) and `Example.book_name` the human name
  (shown in the list). `find_examples_for_word` sorts results into canonical order: text layer
  first (mūla→att→ṭīkā→aññā by extension), then piṭaka within each layer
  (vinaya→sutta→abhidhamma→aññā by filename prefix). Helpers `book_label` /
  `_canonical_sort_key` + optional `Example.book_name` field.
- HIGHLIGHT (2026-06-16, user request): added shared `highlight_terms(text, terms)` to
  `gui2/flet_functions.py` (per-phrase inline tint: candidate word blue, search phrase amber,
  in both Pāḷi + English). Pass2x uses it; example Pāḷi/English wrapped in `ft.SelectionArea`
  (Flet 0.28.3 ignores `Text.selectable`) so text is copyable.
- OUT-OF-SCOPE EDIT — SEPARATE COMMIT AT FINALIZE: `gui2/pass2_pre_view.py` was switched from
  whole-text amber (`_apply_search_highlight`/`_simple_highlight`, removed) to the shared
  `highlight_terms`. Commit this independently of the pass2x thread. (User: still testing.)
- BUGFIX (2026-06-17): niggahita whole-word regex was built with a chained
  `.replace("ṃ","[ṃṁ]").replace("ṁ","[ṃṁ]")` — the 2nd replace re-processed the `ṁ` inserted
  by the 1st, producing the malformed class `disākāka[ṃ[ṃṁ]]` that never matched. So EVERY
  candidate containing a niggahita silently returned 0 translation examples. Fixed both
  occurrences (`find_examples_for_word`, `_mark_word`) with
  `re.sub("[ṃṁ]", "[ṃṁ]", re.escape(word))`. (The commentary, example #0, always showed
  regardless — only the translation search was affected.)
- FEATURE (2026-06-17, user): the "Word in text" field is editable — Enter re-runs the
  example search (`controller.search_word`) for the typed word and refreshes results, keeping
  the current headword and all other fields constant. Commentary #0 shown only if the word was
  harvested. `search_word` reports the hit count in the message field (fixes a stuck
  "searching examples…").
- FEATURE (2026-06-17, user): added a "New" button, identical layout (Yes·No·New·Pass) and
  behaviour to Pass2Pre — opens the "meaning of the new word?" dialog and saves via the shared
  `Pass2NewWordManager` (`pass2_new_words.json`); records without advancing.
- MATCH MODE (2026-06-17, user): `find_examples_for_word` is "starts with" (prefix), not exact
  whole-word — verifier keeps the leading word boundary, drops the trailing one, so a stem
  (`disākāka`) matches `disākākaṃ`, `disākāke`, … Lets the user delete an ending and re-search.
- RULE (2026-06-17, user, final after iterations): `needs_commentary_example` is
  `not meaning_1 and not source_1` — a matched headword must lack BOTH `meaning_1` and
  `source_1` (either present → excluded). Strictest form; narrower than the original
  `not (meaning_1 and source_1)` OR. Supersedes earlier spec decisions on this predicate.
