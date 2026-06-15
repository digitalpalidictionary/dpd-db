# Spec: lookup_prefilter

## GitHub issue
#157 — ongoing refactoring issue (do NOT close; ongoing).

## Overview
The `lookup` table is the biggest in the db (>1M rows). Several call sites load
the **whole** table with `db_session.query(Lookup).all()` and then discard most
rows in Python with an `if` condition. Push that `if` into a SQL `.filter(...)`
so SQLite only returns the rows that are actually used — same behaviour, far
less data crossing the ORM boundary.

All `Lookup` text columns are `Mapped[str]` with `default=""` and are
**non-nullable** (`db/models.py:215-231`). Therefore:
- `if row.col:` (Python truthiness) is **exactly equivalent** to
  `.filter(Lookup.col != "")` — no `None` is ever possible.
- `.filter(Lookup.col.isnot(None))` matches **every** row (it is a no-op).

## Audit of every `Lookup` call site

### A. Full-table load → filtered in Python (the target pattern)
1. **`db/app/create_app_db.py:80-83`** — `query(Lookup).all()` then
   `[(lu.lookup_key, lu.headwords) for lu in lookup_results if lu.headwords]`.
   Textbook case. Fix: `.filter(Lookup.headwords != "")`. Only two columns are
   used, so optionally narrow to `query(Lookup.lookup_key, Lookup.headwords)`.
   Fully behaviour-preserving.
2. **`exporter/sutta_central/sutta_central_exporter.py:120`** — builds a dict of
   the entire table, but `lookup_dict` is only ever read by keys in
   `self.sc_word_set` (`make_sc_dict`). Fix: query only those keys via chunked
   `.in_()` (chunk_size 900, mirroring `kindle_exporter.py:115`). Saved JSON
   (`sc_dict_compiled`) identical: a word absent from the dict and a word with an
   empty entry both route to `no_entries_list` in `compile_sc_dict`. Only
   DEBUG-only counts change. (A weaker
   `.filter(headwords != "" | deconstructor != "")` was tried first but barely
   reduces — nearly every lookup row has `headwords` — so it was replaced by the
   word-set filter.)
3. **`exporter/kobo/kobo.py:102`** — loads the whole table (its
   `.filter(... .isnot(None) ...)` is a dead no-op: cols default `""`, never
   `None`), then keeps `lu.lookup_key in g.word_set` in Python. Fix: query only
   the word-set keys via chunked `.in_()` (chunk_size 900), dropping the dead
   column filter. Behaviour-preserving — `lookup_key` is the PK, chunks are
   disjoint, and the result is re-sorted (`pali_sort_key`) at line 115 either way.

### B. Already pre-filtered (no action)
deconstructor_exporter, goldendict/export_epd, grammar_dict, kindle, pdf,
tbw, tpr, variants_exporter, scripts/build/api_ca_eva_iti_iva_hi,
scripts/find/decon_errors_finder, tools/deconstructed_words,
tools/docs_changelog_and_release_notes, tools/lookup_sync,
exporter/webapp/preloads, scripts/fix/variant_cleaner, gui2/database_manager:216.

### C. Light queries (single column or by-key — no full-row waste)
scripts/find/comm_not_in_decon_finder, scripts/fix/fix_synonym_entries
(both `query(Lookup.lookup_key)`), webapp/toolkit (by-key `ilike`),
gui2/database_manager by-key lookups, scripts/tutorial/quick_start.

### D. Genuine full-table need (leave as is)
**`db/lookup/transliterate_lookup_table.py:165`** — the whole table is needed:
batch processing relies on per-row line-index alignment (blank lines kept for
skipped rows) and the final write-back loops over every row. Pre-filtering would
break the index alignment for marginal gain (`_should_transliterate` already
covers most rows).

### E. Re-swept for missed sites (was incomplete on first pass)
A second whole-repo sweep (incl. tests) confirmed `kindle:118` (chunked + by-key),
`analyzer:785` (by-key `.first()`), `test_idioms:62` (by-key `.first()`) are all
already optimal. The kobo site (now #3 above) was initially mis-filed here as a
"latent bug, out of scope" — it is in fact the strongest candidate and is now
fixed.

## Other tables (DpdHeadword, DpdRoot, …)
Much smaller (~80k headwords, ~2k roots), so gains are minor. The same
*column-narrowing* idea applies where only one attribute is consumed — e.g.
`scripts/fix/variant_cleaner.py:19` does `query(DpdHeadword).all()` only to build
a `lemma_clean` set and could be `query(DpdHeadword.lemma_clean)`. Recommend NOT
churning these broadly; address only if a specific build step is a measured hotspot.

## Constraints
- Behaviour must be identical (saved artifacts byte-for-byte). Debug-only print
  counts may differ where noted.
- Modern type hints, `Path`, no `sys.path` hacks.

## How we'll know it's done
- `create_app_db.py`, `sutta_central_exporter.py`, and `kobo.py` pre-filter at
  SQL level (chunked `.in_()` for the two word-set sites).
- ruff check + format + pyright clean on touched files; related tests pass.
- Other-tables note reported to user.

## What's not included
- No transliterate change (genuine full-table need). No broad
  DpdHeadword/DpdRoot refactor (too small to matter; column-narrowing only).
