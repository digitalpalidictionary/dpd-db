# Spec: Makedict Pipeline Optimizations

## Overview

Optimize the makedict build pipeline for speed. The current pipeline takes ~20 minutes.
Profiling (log: `logs/makedict_2026-06-29_18-31-47.html`) identified five high-impact
bottlenecks. This thread implements targeted fixes for each, with readability and
testability as secondary goals.

All changes must work in both build environments: local makedict AND the GitHub
Action `.github/workflows/draft_release.yml` (which runs Python 3.12 on ubuntu-latest).

The user has already recently optimized `exporter/goldendict`, `exporter/deconstructor`,
`exporter/grammar`, and is working on `exporter/kindle` — those areas are out of scope.

## What it should do

### 1. `sync_lookup_column` → raw SQL upsert (~404s → ~5s)

**Corrected numbers (2026-07-06):** the profiling log shows "syncing headwords column"
at **403.8s** — the ~208s figure previously cited here belongs to "compiling grammar
data", a different stage. This is the single largest item in the thread.

The `add_i2h_to_db()` function in `db/inflections/inflections_to_headwords.py` calls
`tools/lookup_sync.py:sync_lookup_column()` which processes ~449K entries across ~500
SQLAlchemy-chunked query+commit rounds. Replace with a single `executemany` upsert on
the session's own connection:

```sql
INSERT INTO lookup (lookup_key, headwords, <other cols as ''>) VALUES (?, ?, '', ...)
ON CONFLICT(lookup_key) DO UPDATE SET headwords = excluded.headwords
```

**NOT `INSERT OR REPLACE`** (the original design here): that replaces the *whole row*,
blanking the other 16 columns — the live db has 861,713 rows with `deconstructor`
populated before this step runs, which would all be wiped.

Stale handling (`clear_stale`) keeps its exact semantics, implemented in SQL: stage
incoming keys in a temp table, DELETE stale rows whose only value was the target
column, UPDATE the column to `''` on stale rows that still hold other values.
`is_another_value()` stays as-is for the ORM path; the raw path folds the same check
into the DELETE's WHERE clause.

Benchmarked on a copy of the live db: 449K-entry upsert in **4.1s** with all 861,713
`deconstructor` rows intact.

### 2. Tarballing: bz2 → zstd (~395s → ~5s) — DEFERRED, needs release coordination

**Corrected assumption (2026-07-06):** Python `tarfile` has NO zstd support until
Python 3.14 (PEP 784) — the project pins 3.13 and the GitHub Action uses 3.12, so
`tarfile.open(mode="w:zstd")` fails in both environments. Implementation must shell
out to the `zstd` CLI (present locally and on ubuntu-latest runners) or use the
`zstandard` package.

Measured on the 2.2GB db: Python `tarfile w:bz2` = 379.3s / 209MB (matches the log's
394.9s); `tar | zstd -9 -T0` = 4.08s / 257MB (93× faster, +23% size); roundtrip
byte-identical, extraction 1.6s.

**Blast radius:** renaming the release asset `dpd.db.tar.bz2` breaks `tar -xj`
consumers: `draft_release.yml` (lines 328, 444), `justfile`, `scripts/server/update-dpd.sh`,
`CONTRIBUTING.md`, three docs pages, onboarding tests, and any external user's download
script. Deferred to its own thread with a coordinated transition.

### 3. Cache deconstructor words extraction (~3.8s → <0.5s)

`tools/deconstructed_words.py:make_words_in_deconstructions()` queries 861K rows,
calls `json.loads()` and string-splits each one. Cache the resulting word set in a
pickle file keyed by a hash of the deconstructor output. Only recompute when the
deconstructor output changes.

### 4. Transliteration: eliminate per-batch JSON disk I/O (~186s → ~80s)

Both `db/inflections/transliterate_inflections.py` and
`db/lookup/transliterate_lookup_table.py` write JSON files to disk, shell out to
node.js, and read JSON back — for every multiprocessing batch. Replace file I/O
with stdin/stdout piping to the node.js process.

### 5. Merge transliteration engines (~80s → ~40s)

Both transliteration scripts call aksharamukha *and* a separate node.js "path nirvana"
transliterator, merging results. If the orthographic differences are acceptable,
consolidate to one engine. At minimum, eliminate redundant work when outputs agree.

## Assumptions & uncertainties

- ~~Python 3.13's `tarfile` supports `w:zstd` mode~~ **FALSE** — zstd lands in
  Python 3.14 (PEP 784). See #2: must use zstd CLI or `zstandard` package.
- Deconstructor output is the Go JSON file at `pth.go_deconstructor_output_json`.
  File mtime or a hash of its contents can serve as the cache invalidation key.
- Path nirvana node.js scripts (`db/inflections/transliterate inflections.mjs`,
  `db/lookup/transliterate_lookup.mjs`) can read from stdin and write to stdout.
- **Uncertainty:** Whether consolidating to a single transliteration engine produces
  acceptable orthography. The node.js scripts produce different Sinhala/Devanagari/Thai
  output that downstream consumers may rely on. Decision: keep both engines but
  eliminate the disk I/O; don't merge unless byte-identical output is confirmed.

## Constraints

- Must not break the existing Lookup sync protocol used by other scripts
  (`db/variants/add_to_db.py`, `db/lookup/see.py`, etc.)
- Must work in both local makedict and `.github/workflows/draft_release.yml`
  (Python 3.12, ubuntu-latest)
- Transliteration output must remain byte-identical to current output
- Cache invalidation must be automatic (no manual steps)
- All changes must pass the existing test suite (`uv run pytest tests/`)
- Must follow project conventions: `pathlib.Path`, modern type hints, no `sys.path` hacks

## How we'll know it's done

1. **For #1:** Raw `sync_lookup_column` benchmark: <10s for 449K entries (vs 403.8s).
   Tests in `tests/tools/test_lookup_sync.py` pass on both ORM and raw paths;
   `tests/db/inflections/test_inflections_to_headwords.py` passes.
2. **For #2:** Deferred to its own thread.
3. **For #3:** `make_words_in_deconstructions()` returns in <0.5s on cache hit.
   Output identical to current.
4. **For #4:** No JSON files written to disk during transliteration. Output byte-identical.
5. **For #5:** Output byte-identical with one engine removed where safe.
6. **Overall:** Full `uv run pytest tests/` passes.

## What's not included

- Orchestration-level parallelism (multi-exporter, multi-process makedict)
- Optimizing exporters already touched: goldendict, deconstructor, grammar, kindle
- PDF compilation parallelism (deferred, needs typst investigation)
- Database schema changes
- Changes to the Go deconstructor binary
- The tarball zstd switch (#2) — deferred to its own thread
