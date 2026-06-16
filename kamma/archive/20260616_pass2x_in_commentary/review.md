# Review: pass2x_in_commentary (data proof, TUI only)

## Verdict: PASSED

Reviewed iteratively with the user across four live runs; the user inspected the
step TSVs and terminal output at each stage, gave feedback, and confirmed "very
happy" with the final result.

## Objective
Stage 1 of the Pass2x "in commentary" feature: a read-only TUI that finds words
in the `commentary` column which are inflected forms of still-incomplete
headwords, and shows the Pāḷi sentences (with English) they occur in — proving
the data before any GUI is built. Deconstructor lookup deferred (commented).

## Files changed
- `gui2/pass2x/in_commentary_tui.py` — the data-proof TUI (new)
- `gui2/pass2x/in_commentary_exceptions.py` — exceptions manager (new)
- `gui2/pass2x/in_commentary_exceptions.txt` — seeded exceptions list (new)
- `.gitignore` — ignore `gui2/pass2x/data/` (regeneratable diagnostic TSVs)

## Findings & fixes applied (from the iterative review)
1. Over-engineered first cut (deconstructor + variant/spelling filters) → cut
   back to the simplest core: match only on `inflections_list_all`; deconstructor
   commented for later.
2. step4 TSV exploded to 430 MB and split examples across rows/columns → made it
   one row per word, all examples in a single `examples` column, text truncated.
3. Wrong "incomplete" predicate: reused `is_missing_sutta_example`, which (being
   a Pass2pre rule) treats commentary-only examples as still-missing. For Pass2x a
   commentary example counts. Fixed to `not (meaning_1 and source_1)`; verified
   `ṭhātukāma` (id 81184, has `meaning_1` + `source_1=DNa21.10`) is now excluded.
4. Over-eager matches (particles, single letters) → importable/exportable
   exceptions list, seeded and applied.
5. Example #1 must be the commentary the word was pulled from → harvest records
   provenance; commentary shown first, then translation paragraphs.

## Test evidence
- Four successful end-to-end runs (`uv run gui2/pass2x/in_commentary_tui.py`,
  exit 0). Final run: 24,667 commentary rows → 88,273 words → 18,374 matched
  (26 excluded by exceptions), 422,484 translation rows scanned, ~14s total.
- Spot-checks confirmed: `ṭhātukāme` excluded; seeded exceptions (`a`,`ca`,`na`,
  `ti`) removed; example #1 is the `[commentary: …]` entry with the word bolded;
  4,966 words resolve to >1 headword.
- `uv run ruff check` and `uv run pyright` clean on both new modules.

## Out of scope (future threads)
Deconstructor/compound lookup, variant/spelling exclusions, the Pass2x Flet tab,
yes/no/pass choices + persistence, and pass2auto wiring.
