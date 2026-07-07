# Review: Makedict Pipeline Optimizations

**Verdict: PASSED** (2026-07-08)

Review performed live in-session (main thread reviewed a Sonnet subagent's
implementation for each phase): line-by-line diff review, semantic-equivalence
checks, lint/type gates, benchmarks on live-db copies, and user real-run testing.

## Scope delivered

- **Phase 1** — `sync_lookup_column` raw SQL path (implemented, user-tested)
- **Phase 4** — transliteration raw SQL write-back (implemented, user-tested)
- **Phase 2** — zstd tarballing: dropped by user decision (release-asset rename
  coordination outweighs ~375s gain; measurements preserved in spec.md)
- **Phase 3** — deconstructor words cache: dropped by user decision (~5s real gain)
- **Phase 5** — merge transliteration engines: skipped (node engine measured at
  ~1.1s/batch across 22 parallel batches — negligible)

## Files changed

- `tools/lookup_sync.py` — added `use_raw_sql` param + `_raw_sql_sync()`
- `db/inflections/inflections_to_headwords.py` — opts into raw path
- `db/inflections/transliterate_inflections.py` — `_write_translit_to_db()`
  executemany write-back; printer now starts before the ~13s db load
- `db/lookup/transliterate_lookup_table.py` — `_write_translit_to_db()`
  executemany write-back, iterates `translit_dict` directly
- `tests/tools/test_lookup_sync.py` — all 9 tests parametrized orm/raw_sql
- `tests/db/inflections/test_transliterate_inflections.py` — new (4 tests)
- `tests/db/lookup/test_transliterate_lookup_table.py` — new (3 tests)

## Findings and fixes during the thread

1. **Spec's original Phase 1 design (`INSERT OR REPLACE`) was data-destroying** —
   it replaces whole rows, wiping the other 16 lookup columns (861,713 populated
   `deconstructor` rows). Fixed before implementation: `INSERT ... ON
   CONFLICT(lookup_key) DO UPDATE SET {col} = excluded.{col}`.
2. **Spec's Phase 1 number was wrong** — the ~208s figure belonged to "compiling
   grammar data"; the real cost was 403.8s ("syncing headwords column").
3. **Spec's Phase 2 assumption was false** — Python `tarfile` has no zstd until
   3.14 (project pins 3.13; CI uses 3.12). Correct approach (zstd CLI) measured
   and recorded, then dropped by user decision.
4. **Spec's Phase 4 premise was false** — per-batch JSON disk I/O measured at
   ~0.06s total, not ~106s. Real cost was the ORM write-back (107.7s). Phase
   redesigned to the Phase 1 raw-SQL pattern before implementation.
5. **Empty-data edge in raw path** — empty `executemany` parameter lists raise in
   the sqlite3 driver; guarded with `if data:` / `if rows:` (identical no-op
   semantics, covered by tests).

## Test evidence

- Full suite: **1229 passed, 0 failed** (9 earlier analyzer failures proven to be
  local db state — partially built headwords column — not regressions)
- `tests/tools/test_lookup_sync.py`: 18 passed (9 × orm/raw_sql), exact
  updated/inserted/cleared/deleted count equivalence
- New transliteration tests: 7 passed, incl. byte-equality of written values vs
  real `*_pack` methods and untouched-row/column survival
- ruff check + ruff format + pyright: clean on every touched file

## Performance evidence

| Stage | Before | After | Where measured |
|---|---|---|---|
| syncing headwords column | 403.8s | 33.7s | user real run 2026-07-07 |
| inflections write to db | 48.2s | 14.1s | user real run 2026-07-08 |
| lookup write to db | 59.5s | 14.9s | live-db copy benchmark |

~450s (~7.5 min) saved per makedict run. Committed by user as
`#157 lookup_sync: ...` and `#157 transliterate: ...`.
