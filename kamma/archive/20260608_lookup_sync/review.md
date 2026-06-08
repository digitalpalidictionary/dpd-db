## Thread
- **ID:** `20260608_lookup_sync`
- **Objective:** DRY refactor of the Lookup add/update/clear/delete mechanism — one
  shared scoped helper replacing the per-script copy-paste, fixing the see/spelling
  stale-clearing bug and the perf waste of loading the full 1.29M-row table.

## Files Changed
- `tools/lookup_sync.py` — new `sync_lookup_column()` + `LookupSyncResult`; scoped
  add/update/clear/delete, chunked `in_()`, commits internally.
- `tests/tools/test_lookup_sync.py` — 9 behavioural tests against in-memory sqlite.
- `db/grammar/grammar_to_lookup.py` — migrated `add_to_lookup_table` (34 lines → 3).
- `db/lookup/see.py` — migrated; fixes dead `test_set` branch (stale now cleared);
  dropped eager full-table load.
- `db/lookup/spelling_mistakes.py` — same migration + fix.
- `tests/db/lookup/test_see_population.py` — replaced the fake raw-sqlite3 test with a
  real one driving `load_see_dict` + `add_see`.
- `db/epd/epd_to_lookup.py`, `db/families/family_root.py`,
  `db/inflections/inflections_to_headwords.py`,
  `scripts/build/deconstructor_output_add_to_db.py` — migrated; each drops its
  full-table `query(Lookup).all()`.
- `db/variants/add_to_db.py` — migrated (`pack_attr="variants_pack"`) + optional
  `db_session` injection; fixes latent variant-only delete-then-not-readd bug.
- `tests/db/variants/test_add_to_db.py` — replaced characterization test with 4 real
  behavioural tests.
- `kamma/threads/20260608_lookup_sync/{spec,plan}.md` — thread docs.

## Findings
- **CodeRabbit (1, major):** deconstructor should commit before `close()`. **Validated
  as a false positive** — `sync_lookup_column` commits after the stale pass and once per
  chunk, so data persists before `close()`.

## Fixes Applied
- Did not add redundant commits. Addressed the reviewer's wrong assumption at the root by
  documenting the helper's commit contract in its docstring.

## Test Evidence
- `uv run pytest tests/` → `500 passed` (4 pre-existing deprecation warnings).
- `uv run pytest tests/tools/test_lookup_sync.py` → `9 passed`.
- `uv run pytest tests/db/lookup/test_see_population.py` → `5 passed`.
- `uv run pytest tests/db/variants/test_add_to_db.py` → `4 passed`.
- Grammar golden masters before/after migration → `4 passed` both ways (data-gen path
  unchanged).
- ruff check + ruff format + pyright → clean on every touched file.
- `coderabbit review --agent` → 1 finding, validated false positive (see above).

## Deferred (follow-up threads, under #157)
- `suttas_to_lookup.py` (delete-orphans-only), `transliterate_lookup_table.py`
  (update-only, multiprocessing), `help_abbrev_add_to_lookup.py` (multi-column).
- `variants_pack` → `variant_pack` rename → parked thread `20260608_variant_pack_rename`.
- `update_test_add` now has one live caller (suttas); retire once that migrates.

## Verdict
PASSED
- Review date: 2026-06-08
- Reviewer: Claude (Kamma review) — coderabbit-assisted
