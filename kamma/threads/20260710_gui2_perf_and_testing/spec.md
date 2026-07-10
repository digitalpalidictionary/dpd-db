# Spec: gui2 Performance, Resource Use & Testability

**Thread:** 20260710_gui2_perf_and_testing
**GitHub issue:** #157
**Status:** planned

## Problem

The build pipeline has been refactored head to toe; gui2 (~20k lines, 70 files)
has not. Three independent review passes (speed, resource use, testability) plus
direct code reading found systemic problems, catalogued in `findings.md`:

1. **Speed** — everything is eager: 15 tabs and ~25 managers built before first
   paint, a 74 MB JSON parsed at every launch, the full ~83k-row headword table
   loaded on the UI thread on first tab click (and reloaded twice more by pass1/
   pass2 flows, and once per test run, and once per word *saved*).
2. **Resource use** — every `get_db_session()` builds a new SQLAlchemy Engine and
   `new_db_session()` never closes the old one, on paths hit once per word
   navigation; multi-hundred-MB resident structures held for features that may
   never be used.
3. **Testability** — `Gui2Paths` is not injectable so tests would hit real user
   data; ~11 classes do disk/DB I/O in `__init__`; a large body of already-pure
   logic simply lacks tests.
4. **DB tab (user-reported)** — the filter tab locks up and enters weird states:
   unlimited default result set, a multiline TextField control per cell, all work
   synchronous on the UI thread, double session churn per apply, and one
   full-table background reload per row saved.

## Goal

Work through the findings area by area. **Nothing is refactored on speculation:
each area starts with a benchmark and/or characterization tests, and the
decision of what (if anything) to change is made from those numbers.** Behavior
is preserved unless a change is explicitly agreed.

## Non-goals

- No feature changes, no UI redesign beyond what fixing the DB tab requires.
- No big-bang rewrite of ToolKit/controllers; the view-`Protocol` refactor
  (findings F8) is out of scope for this thread — revisit after.
- No changes to the build pipeline, exporters, or db/ modules beyond
  `db/db_helpers.py` engine caching if benchmarks justify it.

## Approach

Ordered phases; each phase = **measure → decide (checkpoint with user) →
implement → verify**. Tests come first so refactors have a safety net.

### Phase 1 — Test safety net (zero-refactor)
Write tests for logic that is already pure (findings F4): `dpd_fields_functions`
(esp. `find_stem_pattern`, `make_lemma_2`, `make_construction`),
`needs_example`, `DbTestManager` core, additions/corrections helpers. Match
existing conventions (in-memory SQLite, `object.__new__`, tmp_path).

### Phase 2 — Testability infrastructure
Add `base_dir` to `Gui2Paths` mirroring `ProjectPaths` (findings F1); route
hardcoded `temp/` writes through `ProjectPaths` (F2). Then instantiate-normally
tests for the JSON file managers (F5).

### Phase 3 — Benchmark harness + baselines
A small repeatable harness (scripts or pytest-bench style) measuring, on a
throwaway copy of dpd.db:
- cold startup to first paint (and per-stage: ToolKit, each view, pre-init queries)
- memory RSS after launch, after first tab click, after N word navigations
- engine/session creation cost in isolation (current vs cached-engine prototype)
- DB tab: apply-filter wall-clock at limits 0/100/1000/10000 rows
- corpus load + RelationshipDetector build time
- JSON file manager write cost at real file sizes
Baselines recorded in the thread; every later phase re-runs the relevant probe.

### Phase 4 — Engine/session hygiene (Theme A)
As built: cache one Engine per db path in `db/db_helpers.py`, with a
**NullPool** (a bounded shared pool exhausts and 30s-blocks because gui2
keeps many never-committed sessions alive, each pinning a connection — found
by user smoke test as a live `QueuePool limit ... reached` crash), a thread
lock, and a fork-PID guard. `new_db_session()` deliberately does NOT close
the previous session — Flet handlers run in a thread pool and the old session
may still be running another tab's query (close() kills it mid-fetch).
External-commit visibility preserved (probe-verified with a live sqlite3
side-writer); abandoned sessions free their connections via the cyclic GC.

### Phase 5 — DB tab fix (Theme D, user priority)
Decide from Phase 3 numbers among: default row limit + paging; read-only cells
with edit-on-demand; off-thread query/build; single commit + single detector
invalidation per save batch; stable row keys (id, not index).

### Phase 6 — Corpus load discipline (Theme B)
Single cached corpus load, off the UI thread; pass1/pass2/tests derive from it;
detector rebuilds serialized and debounced.

### Phase 7 — Lazy startup (Theme C)
Lazy `cached_property` managers on ToolKit; lazy tab content on first selection;
lazy 74 MB wordfinder JSON; lazy AI providers; drop uvicorn `--reload`;
`DISTINCT` in the pre-init queries. Each item accepted/rejected on its measured
startup contribution.

### Phase 8 — JSON write amplification (Theme E) — measure-first, may be a no-op
Only act where Phase 3 shows real cost (pass1 8 MB rewrites, pass2_auto
read+write per item).

## Success criteria

- All new tests pass; full `uv run pytest tests/` stays green throughout.
- Every touched file passes `ruff check`, `ruff format`, `pyright`.
- Benchmarks show measured improvement for each accepted change, recorded
  before/after in the thread.
- The DB tab no longer locks up with the default preset.
- GUI behavior otherwise unchanged (manual smoke test by user at each phase end).
- One commit per phase (see `plan.md` § Commit cadence). `/cm` only drafts the
  commit message — the user stages and commits themselves; I never run any
  git write command.

## Assumptions & uncertainties

- `new_db_session()` exists partly to see data committed by external processes;
  any session reuse must preserve that (use `expire_all` or fresh session from a
  shared engine — to verify in Phase 4).
- Flet control-tree size is assumed to be the DB tab lockup mechanism; Phase 3
  benchmark will confirm before Phase 5 commits to a UI change.
- Startup numbers are unknown until measured; lazy-loading order within Phase 7
  will be set by the Phase 3 per-stage breakdown.
- User runs the GUI manually for interactive verification; automated tests
  cannot cover live Flet rendering.

## Dead code

Unreachable branches / code found incidentally while working the phases above.
Out of scope for this thread (see scope rule — noticed, not touched); logged
here as a running list for a future cleanup pass. Append to this list, don't
open a new phase for it.

- `gui2/dpd_fields_functions.py` `find_stem_pattern` — masc `"rāja masc"`
  branch (~line 157) and fem `"mātar fem"` branch (~line 187) are unreachable:
  an earlier, broader `endswith` check in the same `elif` chain always matches
  first. Found while writing Phase 1.1 tests.
- `gui2/dpd_fields_functions.py` `make_compound_construction_from_headword` —
  the `dvanda` branch is unreachable whenever `grammar` contains the word
  "comp", because the compound-check `elif` above it matches first. Found
  while writing Phase 1.1 tests.
