# Review: lookup_prefilter

**Verdict: PASS**

## Scope
Two behaviour-preserving SQL pre-filters on the >1M-row `lookup` table, replacing
"load all → filter in Python" with "filter in SQL".

## Behaviour-preservation analysis

### `db/app/create_app_db.py:81-86`
- Before: `query(Lookup).all()` then `[(k, h) for lu in rows if lu.headwords]`.
- After: `query(Lookup.lookup_key, Lookup.headwords).filter(Lookup.headwords != "").all()`
  then `[(k, h) for lu in rows]`.
- `Lookup.headwords` is `Mapped[str]`, non-nullable, `default=""`, so
  `headwords != ""` is exactly the truthiness test that was in Python. The
  produced `lookup_data` tuples — and thus the mobile-db `INSERT` — are identical.
- Column-narrowing is safe: only `lookup_key`/`headwords` were ever read; Row
  objects expose both as named attributes.

### `exporter/sutta_central/sutta_central_exporter.py` — chunked `.in_()`
- `lookup_dict` is only ever read by keys in `self.sc_word_set` (`make_sc_dict`,
  line 145-146). `make_lookup_dict` now queries only those keys via chunked
  `.in_(chunk)` (chunk_size 900) instead of `query(Lookup).all()`.
- Membership semantics for any `word ∈ sc_word_set` are unchanged: `word in
  lookup_dict` iff the word exists in the lookup table — exactly as before.
- `compile_sc_dict` routes both empty-entry and absent words to
  `no_entries_list`, so the saved `sc_pli2en_dpd.json` is identical. Only
  DEBUG-only counters differ.
- (An interim `headwords != "" | deconstructor != ""` filter was replaced — it
  barely reduced rows since nearly every lookup row has `headwords`.)

### `exporter/kobo/kobo.py` — chunked `.in_()`
- Before: `query(Lookup).filter(... .isnot(None) ...)` (a no-op — cols default
  `""`, never `None`, so all ~1M rows load) then `[lu ... if lu.lookup_key in
  g.word_set]`.
- After: chunked `query(Lookup).filter(Lookup.lookup_key.in_(chunk)).all()` over
  `word_set` (chunk_size 900), dead column filter removed.
- Identical result set: `lookup_key` is the PK, `word_set` is a set, chunks are
  disjoint → no dup/missing rows; line 115 re-sorts by `pali_sort_key` either way.

## Gate
- `ruff check`, `ruff format`, `pyright`: clean on both files.
- Cleared pre-existing gate-blockers: sutta_central (RUF012 → `ClassVar`,
  EXE001 → chmod 775) and kobo (EXE001 → chmod 775), matching siblings
  tbw/variants.
- `tests/exporter/sutta_central/test_sutta_central_exporter.py`: 21 passed.
  (kobo has no test file; change mirrors the proven `kindle` idiom.)

## Process note
First pass mis-scoped kobo as an out-of-scope "latent bug" and gave sutta_central
a weak filter. A second sweep + user challenge corrected both to the chunked
`.in_()` form. Lesson recorded in `kamma/lessons.md`.

## Reported separately (not implemented)
- **transliterate_lookup_table.py** — genuine full-table need (index alignment +
  write-back); left as is.
- **Other tables** — DpdHeadword/DpdRoot too small to matter; only column-
  narrowing applies (e.g. `variant_cleaner.py:19`), recommend not churning.
