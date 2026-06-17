# Review: pass2x_flet_tab

## Verdict: PASSED

Built and refined iteratively with the user live in the GUI across many feedback
rounds; the user confirmed "It's working really nicely now. I'm happy with the
results."

## Objective
Stage 2 of Pass2x "in commentary": the real Flet tab (between Pass2Pre and
Pass2Auto) with a selectable, filterable example list and Yes/No/New/Pass
choices, persisting "yes" results in the `matched` shape Pass2Auto consumes.

## Files
- **NEW** `gui2/pass2x/in_commentary_controller.py` — controller (load → walk
  words → per-word JIT example search → walk headwords → yes/no/new/pass).
- **NEW** `gui2/pass2x/in_commentary_view.py` — the Pass2x tab view.
- **EDIT** `gui2/pass2x/in_commentary_tui.py` — additive `find_examples_for_word`
  (per-word, uncapped, "starts with" prefix match, canonical sort, human book
  names); `Example` gained `book_name` + `is_commentary`; niggahita regex bugfix;
  final incomplete rule `not meaning_1 and not source_1`.
- **EDIT** `gui2/main.py` — register the Pass2x tab; fix `_get_current_lemma` map.
- **EDIT** `gui2/pass2_auto_control.py` — add `"in_commentary"` pseudo-book; guard
  dead `_cst_books`.
- **EDIT** `gui2/daily_log.py` — register `pass2x` key.
- **EDIT** `gui2/flet_functions.py` — shared `highlight_terms` (per-phrase tint).
- **EDIT** `gui2/pass2_pre_view.py` — adopt `highlight_terms` (own commit; see below).

## Key decisions & fixes (from the iterative review)
1. Persistence reuses `Pass2PreFileManager("in_commentary")` → writes
   `pass2_pre_in_commentary.json`, consumed by Pass2Auto with zero format glue
   (only a dead-`_cst_books` guard + dropdown entry needed).
2. Dropped the bulk 18k pre-scan + `EXAMPLE_CAP`; examples found just-in-time per
   word (uncapped), since a session processes ~20 words.
3. Match mode is "starts with" (prefix), not exact whole-word — lets the user
   delete an ending and re-search.
4. Editable "Word in text" (Enter re-searches, headword constant).
5. Commentary is example #0: always shown, copyable (SelectionArea), never
   selectable — keyed off an explicit `is_commentary` flag (not position).
6. Keyword filter + amber per-phrase highlight (shared `highlight_terms`).
7. Machine table names → human book names + DPD code via `cst_book_translator`;
   examples sorted canonically (layer mūla→att→ṭīkā→aññā, then piṭaka).
8. "New" button mirrors Pass2Pre exactly (shared `Pass2NewWordManager`).
9. Incomplete rule settled at `not meaning_1 and not source_1`.

## Bugs found & fixed
- `daily_log.increment("pass2x")` raised (key not whitelisted) → froze the UI
  after "Yes". Registered the key.
- Chained `.replace("ṃ","[ṃṁ]").replace("ṁ","[ṃṁ]")` re-processed its own output
  → malformed regex → EVERY niggahita word returned 0 examples. Fixed with a
  single `re.sub`.
- View assumed "index 0 = commentary" → first result unselectable after a manual
  search of a non-harvested word. Fixed via the `is_commentary` flag.
- `search_word` left a stuck "searching examples…" message → now reports hit count.

## Test evidence
- `ruff check` + `ruff format` + `pyright` clean on every touched file.
- Manual verification by the user in the live GUI (the primary check for Flet
  UI); confirmed Yes/No/New/Pass, filter, prefix re-search, canonical order,
  selectable text, and Pass2Auto consumption of `in_commentary`.
- No automated tests added (Flet UI; project rule: no unasked script execution).

## Known limitation (future follow-up, not a blocker)
`Pass2PreFileManager.matched` is keyed by word, so if one word has multiple
incomplete headwords and the user clicks "Yes" on more than one, only the last
survives (the first is overwritten). Inherited from Pass2Pre; flagged to the user.
Fixing requires keying matched on (word, headword id) and adjusting Pass2Auto's
iteration — its own thread.

## Commit plan (user commits)
1. pass2x thread — all files above EXCEPT `pass2_pre_view.py`, plus the thread
   archive move. Relates to #162 (do not close).
2. `pass2_pre_view.py` — separate commit (shared highlight consolidation), per
   the user's request.
