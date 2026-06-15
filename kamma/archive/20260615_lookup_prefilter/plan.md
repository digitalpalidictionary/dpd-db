# Plan: lookup_prefilter

## Phase 1 — Safe behaviour-preserving pre-filters
- [x] `db/app/create_app_db.py` — narrowed to `query(Lookup.lookup_key,
      Lookup.headwords).filter(Lookup.headwords != "")`; dropped the redundant
      `if lu.headwords` guard.
- [x] `exporter/sutta_central/sutta_central_exporter.py` — `make_lookup_dict`
      now queries only `sc_word_set` keys via chunked `.in_()` (chunk_size 900),
      replacing the interim headwords|deconstructor filter. Cleared 2 pre-existing
      gate-blockers (RUF012 → `ClassVar`, EXE001 → chmod 775).
- [x] `exporter/kobo/kobo.py` — `compile_lookup_data` now queries only
      `word_set` keys via chunked `.in_()` (chunk_size 900), dropping the dead
      `.isnot(None)` filter + the Python membership filter. Cleared pre-existing
      EXE001 (chmod 775). (Initially mis-scoped as out-of-scope; corrected after
      user challenge — it was the biggest win.)

## Phase 2 — Verify
- [x] ruff check + ruff format + pyright clean on both files.
- [x] `tests/exporter/sutta_central/test_sutta_central_exporter.py` — 21 passed.

## Phase 3 — Report (no code)
- [x] Surface kobo `.isnot(None)` dead-filter as a separate decision.
- [x] Note the column-narrowing idea for DpdHeadword/DpdRoot (low priority).

## Status: COMPLETE — reviewed PASS (see review.md). Not committed (user commits).

## Out of scope
- kobo change, transliterate change, broad small-table refactor.
