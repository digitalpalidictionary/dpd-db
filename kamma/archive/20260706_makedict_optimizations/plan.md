# Plan: Makedict Pipeline Optimizations

**Spec:** ./spec.md

## Architecture Decisions

- **Phased by risk, not by speed:** Touching the shared `tools/lookup_sync.py` (#1) is highest-risk (used by 4+ scripts). Do it first so any bugs surface early.
- **Raw SQL path in `sync_lookup_column` is opt-in:** Add a `use_raw_sql=False` parameter. Existing callers continue using the SQLAlchemy path unchanged. Only `inflections_to_headwords.py` opts in, keeping risk contained.
- **Raw path uses the session's own connection** (`db_session.connection().exec_driver_sql`), not a second `sqlite3.connect` — same transaction, no lock contention, commits via `db_session.commit()` like the ORM path.
- **Upsert primitive is `ON CONFLICT(lookup_key) DO UPDATE SET {col} = excluded.{col}`** — never `INSERT OR REPLACE`, which replaces whole rows and wipes the other 16 columns (861K populated `deconstructor` rows).
- **Stale handling in SQL:** incoming keys staged in a temp table; the `is_another_value` check becomes the DELETE's WHERE clause (all other columns empty). No separate helper needed.
- **Values packed via a scratch transient `Lookup()`** using the real `*_pack` methods — byte-identical JSON, zero duplicated pack logic.
- **zstd tarballing (#2) deferred:** Python 3.12/3.13 `tarfile` has no zstd (3.14 feature); needs zstd CLI or `zstandard` package plus a coordinated release-asset rename. Own thread.
- **Deconstructor cache:** Pickle in `temp/deconstructor_words_cache.pkl` with a key derived from `pth.go_deconstructor_output_json.stat().st_mtime`. Fall back to recompute if stale or missing.
- **Transliteration stdin/stdout:** Modify node.js scripts to accept `--stdin` flag. When set, read JSON from stdin, write JSON to stdout. Python side uses `subprocess.Popen` with pipes.

## Phase 1 — `sync_lookup_column` raw SQL path (#1)

- [x] Add `_raw_sql_sync(db_session, column, data, pack_attr, clear_stale)` to `tools/lookup_sync.py`
  - Pack values through a scratch transient `Lookup()` (real `*_pack` methods)
  - Stage keys in a temp table on the session's connection
  - Stale pass in SQL: DELETE rows where only the target column held a value; UPDATE `col=''` on the rest
  - Single `executemany` upsert with `ON CONFLICT(lookup_key) DO UPDATE`
  - Return `LookupSyncResult` with exact updated/inserted/cleared/deleted counts
  - Deviation: `if data:` / `if rows:` guards around the two executemany calls (empty
    parameter lists raise in the sqlite3 driver; guards preserve identical no-op semantics)
  → verified: `uv run pytest tests/tools/test_lookup_sync.py` — 18 passed (9 × orm/raw_sql)

- [x] Add `use_raw_sql=False` parameter to `sync_lookup_column`, dispatching to `_raw_sql_sync`
  - When `False`: existing behavior byte-identical
  → verified: ORM-path tests green and untouched

- [x] Parametrize `tests/tools/test_lookup_sync.py` to run every test on both paths (`orm` / `raw_sql`)
  → verified: full matrix green including exact count assertions

- [x] Update `db/inflections/inflections_to_headwords.py:add_i2h_to_db()` to call `sync_lookup_column(..., use_raw_sql=True)`
  → verified: i2h tests pass; end-to-end benchmark on live-db copy: 449K entries in
    **6.58s** (vs 403.8s, ~61×), exact counts, 861,713 deconstructor rows intact,
    packed JSON byte-identical. Full suite `pytest tests/`: 1213 passed; 9 failures in
    `tests/exporter/analysis/test_analyzer.py` are pre-existing (local dpd.db has a
    partially built `headwords` column — 3,420 rows vs ~449K; db mtime untouched by
    this work)
  → user-tested 2026-07-07 on real db: "syncing headwords column" 444,880 → **33.7s**
    (vs 403.8s, ~12×); whole script 51.9s. Real run is slower than the lab number
    because the stale pass scans a fully populated headwords column and the timed
    section includes building the 444K-entry data dict

## Phase 2 — zstd tarballing (#2) — DROPPED (2026-07-08)

User decision: release-asset rename coordination (external consumers, docs, CI,
onboarding) outweighs the ~375s gain for now. Measured potential recorded in spec.md
if revisited: `tar | zstd -9 -T0` = 4.1s vs 379.3s Python `tarfile w:bz2`.

## Phase 3 — Cache deconstructor words (#3) — DROPPED (2026-07-08)

User decision: real cost measured at 5.7s per run; pickle-cache complexity and
invalidation risk not worth ~5s.

## Phase 4 — Transliteration raw SQL write-back (#4, redesigned 2026-07-07)

Original stdin/stdout design dropped: measured JSON file I/O is ~0.06s total across
22 parallel batches, not ~106s. The .mjs scripts and `_parse_batch` stay untouched.
The real cost is the ORM write-back (48.2s + 59.5s); fix with the Phase 1 pattern.

- [x] Replace the ORM write-back loop in `transliterate_inflections.py:main()`
  - New `_write_translit_to_db(db_session, dpd_db, translit_dict) -> int`, single
    executemany `UPDATE dpd_headwords ... WHERE id=?`, no ORM mutation
  → verified: end-to-end on live-db copy: 89,143 rows in **8.6s** (vs 48.2s, ~5.6×)

- [x] Replace the ORM write-back loop in `transliterate_lookup_table.py:main()`
  - New `_write_translit_to_db(db_session, translit_dict) -> int`, iterates
    `translit_dict` directly (skips the 1.29M-row scan), values via
    `json.dumps(list(...), ensure_ascii=False)` matching `*_pack`
  → verified: end-to-end on live-db copy: 1,290,989 rows in **14.9s** (vs 59.5s, ~4×);
    grammar column intact; packed format byte-identical to `sinhala_pack`

- [x] Tests covering both write-backs against in-memory db with real models
  - `tests/db/inflections/test_transliterate_inflections.py` (4 tests)
  - `tests/db/lookup/test_transliterate_lookup_table.py` (3 tests, incl. byte-equality
    vs real `*_pack` methods)
  → verified: full suite `uv run pytest tests/` — **1229 passed, 0 failed** (the 9
    analyzer failures noted in Phase 1 disappeared once the live db's headwords
    column was rebuilt, confirming they were db-state, not regressions)

## Phase 5 — Merge transliteration engines (#5) — SKIPPED (rescoped 2026-07-07)

Node.js engine costs ~1.1s per batch across 22 parallel batches — negligible.
Merging engines risks orthography changes for no meaningful gain. No work planned.

## Phase 6 — Full pipeline verification

- [x] Run full test suite: `uv run pytest tests/ -m 'not slow'`
  → verified: 1229 passed, 0 failed (2026-07-08)

- [x] Measure the optimized sections on real runs
  → verified: Phase 1 user-tested — syncing headwords column 403.8s → 33.7s;
    Phase 4 user-tested — transliterate_inflections total 37.2s (writing to db 14.1s
    vs 48.2s); lookup write-back verified on live-db copy 14.9s vs 59.5s.
    Combined ~450s saved per makedict run. Full-pipeline timing comparison will
    happen naturally on the next release build
