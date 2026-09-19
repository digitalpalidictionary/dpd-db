# Spec — gui2 db load time

Follow-up to `20260918_gui2_startup_latency`, which made startup faster and
left the database load as the entire remaining wait. No dedicated issue.

## Overview

`DatabaseManager.initialize_db()` (gui2/database_manager.py) takes ~6.9 s
median (three headless runs, 2026-09-18). Measured components from the
startup thread's profiling:

| component | time | what it does |
|---|---|---|
| `load_corpus()` | 3.19 s | full ORM load of 89,559 dpd_headwords rows (~55 columns, 5 big HTML columns deferred) |
| `get_all_decon_no_headwords()` | 1.51 s | scans 1,282,462 lookup rows for headwords=="" and deconstructor!="" |
| `RelationshipDetector(corpus)` | 1.12 s | builds phonetic-variant + synonym contexts over the whole corpus |
| 8 small set queries + overhead | ~0.4 s | lemma/pos/roots/families/patterns sets |
| `pre_initialize_gui_data()` | 0.36 s | five distinct-value queries, runs before initialize_db |

The editor cannot edit until `db_loaded` is set, so all of this sits on the
critical path every launch.

## What it should do

Reduce `initialize_db()` to a target of **≤ 4 s median, from 6.90 s**, with
zero behaviour change — same sets, same detector results, same staleness
semantics (`mark_corpus_stale` / `_corpus_gen` / `_inflections_gen`).

Candidate mechanisms, each to be **validated on a throwaway copy
(`cp dpd.db /tmp/`) before implementation** — the project rule for
optimisation threads; no fix ships on an unbenchmarked claim:

1. **Deconstructor scan.** Either cache the derived set in the `db_info`
   key-value store (invalidated whenever lookup is rebuilt), or make the
   query cheaper (column/index). Only ship what Phase 1 benchmarks faster.
2. **Corpus load.** ORM hydration dominates. Options: `load_only()` a
   verified column list (requires an exhaustive consumer sweep of every
   attribute touched on corpus rows), or keep full entities but skip
   unnecessary query machinery with a raw projection (pattern:
   `tools/lookup_sync.py:_raw_sql_sync`). Whichever benchmarks faster AND
   survives the consumer sweep.
3. **RelationshipDetector off the critical path.** It is only read when the
   user opens a word's related-entries section. Build it lazily on first use
   (ToolKit lazy-manager precedent) instead of inside initialize_db.

Phase 1 re-derives every number from scratch (the 3.19/1.51/1.12 s figures
predate this thread) and picks the winners; no mechanism survives to Phase 2+
unbenchmarked.

## Assumptions & uncertainties

- **Verified:** row counts (89,559 dpd_headwords / 1,282,462 lookup);
  initialize_db's structure; the detector is only constructed in
  initialize_db; corpus staleness is already generation-guarded.
- **Assumed, to verify in Phase 1:** the per-component timings still hold on
  this machine today; which corpus columns consumers actually touch; that
  db_info-caching the deconstructor set can be invalidated correctly (find
  every writer of `lookup.deconstructor`).
- **Assumed:** lazy detector construction doesn't break anything that reads
  `toolkit.db_manager._relationship_detector` directly during warm-up — must
  be grep-verified before Phase 4.

## Dated outcomes (2026-09-19, after implementation)

- The "detector only constructed in initialize_db" claim turned out
  **wrong twice over**: the eager construction was still in initialize_db
  at implementation time (the lazy accessor existed but wasn't what the
  critical path used). Removing the eager line — and pre-building the
  detector in the app warm-up instead — took load_corpus off the critical
  path entirely, because the corpus was only loaded to feed the detector.
- Phase 1 re-derivation: warm-cache component medians are corpus 1.898 s,
  decon 2.221 s, detector 0.687 s, small sets 0.316 s. Cold-process
  launch reality: corpus 3.4-4.3 s, eager detector 0.79-0.91 s.
- Mechanism 1 shipped as a db_info JSON cache, invalidated inside
  `sync_lookup_column` for headwords/deconstructor syncs (covers every
  lookup writer found), rebuilt at the end of generate_components, with a
  live-query fallback + self-heal in gui2.
- Mechanism 2 killed: load_only impossible (tests tab reads 45+ data-driven
  columns on corpus rows); raw core projection benchmarked 2.6× SLOWER;
  fast hydration (`__new__` + `__dict__.update`) only ~0.2 s (row decode,
  not hydration, dominates); execute(select) and SQLite mmap_size within
  noise.
- Mechanism 3 shipped after the correction above; first-stage result
  (decon cache only) was median 5.30 s — missed the ≤ 4 s target and the
  miss prompted the re-test.
- **Final result: db-loaded median 0.82 s (was 6.90 s); fully-warmed
  9.1 s median (was 10.3 s).** Editor usable ~0.8 s after launch;
  corpus/detector load lazily off the critical path.

## Constraints

- No behaviour change visible to the user: same data, same sets.
- Benchmark on a throwaway db copy; never benchmark against the live dpd.db.
- ORM performance rules from AGENTS.md apply (no ORM loops; executemany
  pattern for bulk sync; never INSERT OR REPLACE on lookup).
- Touching a file means owning its lint (ruff check --fix, format, pyright).
- No `git stash`/`checkout --`/`reset --hard` — shared working tree.

## How we'll know it's done

1. Phase 1 table of re-derived per-component timings pasted into plan.md.
2. db-loaded stamp ≤ 4 s median of three, via `artifacts/timed_gui.py` from
   the startup thread (`kamma/threads/20260918_gui2_startup_latency/artifacts/`).
3. `uv run pytest tests/gui2/` and `uv run pytest tests/` pass; `just
   typecheck` clean.
4. No change in the sets/detector outputs (spot-checked against pre-change
   values in Phase 1).

## What's not included

- Anything about `just gui` startup outside initialize_db (done in
  20260918_gui2_startup_latency).
- pass2pre's 11.3 s CST parse (its own follow-up).
- pass2pre stage-by-stage progress feedback (migration-era loss, separate).
- Any change to the db build pipeline or schema.
