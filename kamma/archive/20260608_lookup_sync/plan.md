# Plan: lookup_sync — DRY refactor of the Lookup add/update/clear/delete mechanism

## Architecture
- New module `tools/lookup_sync.py` with `sync_lookup_column()` + `LookupSyncResult`.
- Scoped queries only (copies `db/variants/add_to_db.py`). Never `query(Lookup).all()`.
- Reuses `tools.lookup_is_another_value.is_another_value`.
- Callers keep value prep; they build the `data` dict then call the helper.
- `variant` passes `pack_attr="variants_pack"` until the rename thread lands.
- Incremental rollout, one script per task, all under #157. Pause for review after the
  helper + first migration before doing the rest.

## Phase 1 — the helper (test-first)
- [x] Write `tests/tools/test_lookup_sync.py` against an in-memory sqlite db
  (`tests/gui2/test_roots_db.py` pattern). Cases: update existing row, insert new key,
  clear stale key that has another value, delete stale key with no other value,
  `clear_stale=False` skips the stale pass, `pack_attr` override writes `variant`,
  chunking, mixed-in-one-call. 9 tests, all green.
- [x] Implement `tools/lookup_sync.py` to make the tests pass.
- [x] Gate: `ruff check --fix` → `ruff format` → `pyright` → `pytest tests/tools/test_lookup_sync.py`.

## Phase 2 — migrate grammar (canonical full-load case)
- [x] Replace the hand-rolled loop in `db/grammar/grammar_to_lookup.py::add_to_lookup_table`
  with a `sync_lookup_column(db, "grammar", g.grammar_data)` call. Keep the printer lines.
  (34 lines → 3; dropped unused Lookup / update_test_add / is_another_value imports.)
- [x] Confirm existing golden masters still pass
  (`tests/db/grammar/test_grammar_to_lookup.py` covers data-gen, unaffected). 4 green.
- [x] Gate the touched file + run grammar tests.

→ **CHECKPOINT: stopped here for user review before continuing.**

## Phase 3 — migrate see + spelling (bug fix + behaviour change)
- [x] `db/lookup/see.py`: build `data = {k: pali_list_sorter(v) for ...}`, call
  `sync_lookup_column(db, "see", data)`. Removed the dead `test_set` branch and the
  eager `query(Lookup).all()` in GlobalVars; stale `see` now cleared.
- [x] `db/lookup/spelling_mistakes.py`: same shape for `spelling`; dropped the
  class-level full-table load too.
- [x] Replaced the fake `tests/db/lookup/test_see_population.py` (raw sqlite3, never
  called `see.py`) with a real test driving `load_see_dict` + `add_see` against an
  in-memory db: load-tsv, insert, update, stale-clear-with-other-value, stale-delete.
- [x] Gate touched files + run lookup tests. 28 green across lookup/grammar/suttas/helper.

→ **CHECKPOINT: stopped here for user review before continuing.**

## Phase 4 — migrate epd, family_root, inflections→headwords, deconstructor
- [x] `db/epd/epd_to_lookup.py` (`epd`).
- [x] `db/families/family_root.py::update_lookup_table` (`roots`).
- [x] `db/inflections/inflections_to_headwords.py` (`headwords`) — TPR tsv write
  untouched; only the db add step uses the helper.
- [x] `scripts/build/deconstructor_output_add_to_db.py` (`deconstructor`).
- [~] epd test: SKIPPED deliberately. `epd_to_lookup` runs heavy side effects at import
  time (config check + full `query(DpdHeadword).all()` in the class body), so a clean
  unit test isn't practical without refactoring import-time behaviour (out of scope).
  The migrated write path is a thin `sync_lookup_column` wrapper already covered by the
  9 helper tests; epd's data-gen is unchanged. Noted rather than forcing an ugly test.
- [x] Gate each touched file + `uv run pytest tests/db tests/tools`: 276 passed.

## Phase 5 — wrap up
- [x] `update_test_add` now has ONE live caller: `db/suttas/suttas_to_lookup.py`
  (deferred). Kept. `is_another_value` still used by suttas, help_abbrev, transliterate,
  variants(now via helper) and the helper itself — kept.
- [x] Migrated `db/variants/add_to_db.py` onto the helper (`pack_attr="variants_pack"`).
  Added optional `db_session` injection so the class is testable. This also fixes a
  latent bug: the old delete pass could delete a variant-only row still present in the
  new data and never re-add it. Replaced the stale characterization test with 4 real
  behavioural tests (insert / update-not-lost / stale-delete / stale-clear).
  Note: `tests/db/variants/test_add_to_db_fixtures.json` is now an unused orphan
  (didn't delete it — not mine to remove without a nod).
- [x] Full `uv run pytest tests/`: 500 passed.
- [x] coderabbit review --agent: 1 "major" finding (deconstructor: commit before close).
  Validated as a FALSE POSITIVE — `sync_lookup_column` commits after the stale pass and
  once per chunk, so data persists before `close()`. Did not add redundant commits;
  instead documented the helper's commit contract in its docstring (root cause of the
  reviewer's wrong assumption). Re-gated: green.
- [ ] await user commit go-ahead (unrelated working-tree files excluded:
  `db_tests/db_tests_columns.tsv`, `scripts/project_health_check.py`).

## Deferred (separate threads, under #157)
- `suttas_to_lookup.py`, `transliterate_lookup_table.py`, `help_abbrev_add_to_lookup.py`.
- `variants_pack`/`variants_unpack` rename → thread `20260608_variant_pack_rename`.
