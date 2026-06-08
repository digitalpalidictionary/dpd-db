# Plan: migrate suttas_to_lookup.py + retire update_test_add

Status: **parked** — depends on nothing new; the main thread (`20260608_lookup_sync`)
is done. Pick up any time.

## Tasks
- [x] `db/suttas/suttas_to_lookup.py::add_to_lookup_table`: build
  `data = {code: sorted(ids) for code, ids in g.sutta_info_dict.items()}`, call
  `sync_lookup_column(g.db_session, "headwords", data, clear_stale=False)`. Remove the
  `update_test_add` loop and the bespoke orphan-delete branch.
- [x] Remove the eager `query(Lookup).all()` (`lookup_db`) from `GlobalVars` / `main`
  (no longer needed). Trim unused imports.
- [x] Add a loud note to the module docstring: correctness depends on
  `inflections_to_headwords.py` running immediately before with `clear_stale=True`
  (build order 47 → 50). Standalone runs accumulate stale sutta codes.
- [x] Add `tests/db/suttas/test_suttas_write.py` (in-memory sqlite): existing sutta-code
  updated, new inserted, and an existing inflection `headwords` row (key not in
  sutta_data) left untouched.
- [x] Delete `tools/update_test_add.py`.
- [x] Edit `tests/scripts/build/test_deconstructor_output_add_to_db.py`: remove the
  `TestUpdateTestAdd` class and the `update_test_add` import; keep `TestIsAnotherValue`
  and `TestDeconstructorPack`.
- [x] Confirm no live `update_test_add` references remain (`rg update_test_add`,
  excluding `archive/`).
- [x] Gate touched files + `uv run pytest tests/` (incl. suttas golden master).

## Risk / watch-list
- The ordering dependency is the main risk. If the build sequence is ever reordered so
  suttas runs without inflections clearing first, stale sutta codes return. Document, and
  consider a guard/assertion only if it becomes a real problem.
- Confirm grammar (order 52) running after suttas doesn't touch `headwords` — it writes
  `grammar` only, so it's fine.
