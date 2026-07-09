# Handoff: pyglossary cacheDir/tmp cleanup race

## Thread
- **ID:** 20260709_pyglossary_tmp_cleanup_race
- **Objective:** Eliminate the spurious `no such file or directory: …/pyglossary/tmp` stderr error that fires when `export_to_goldendict_with_pyglossary` runs with `include_slob=True`.

## Status — implementation done, awaiting user manual verification + review

### What was done (Phases 1–3)

**Phase 1 — fix applied:** `tools/goldendict_exporter.py`, `create_glossary()`:
- Added `_ = glos.tmpDataDir` after `Glossary(...)` construction, before `pr.yes("ok")`.
- `ruff check`, `ruff format`, `pyright` all clean on the file.

**Hypothesis proven by execution:** Two `Glossary()` instances each get a unique `cacheDir/<uuid>_res` tmp dir (`…d4a7bdc07bbe…_res` vs `…d4a7cc027bbe…_res`), not the shared `cacheDir/tmp`.

**Phase 2 — regression test:** `tests/tools/test_goldendict_exporter.py` (new):
- `test_create_glossary_has_nonempty_tmp_dir` — fix is active.
- `test_two_glossaries_have_distinct_tmp_dirs` — core race guard.
- `test_glossary_tmp_dir_is_not_shared_cache_dir_tmp` — not the fallback path.
- `test_create_glossary_fix_is_present` — source guard if refactored.
- All 4 pass; ruff/format/pyright clean.

**Phase 3 — smoke gate:** `uv run pytest tests/` → **1249 passed, 16 deselected (slow), 0 failures**.

### What remains

- [ ] **Phase 3 manual verification (user):** run an export with `include_slob=True`, confirm no `no such file or directory` on stderr.
- [ ] **Phase 4:** `/kamma:3-review`, then `/kamma:4-finalize`.

### Files changed
- `tools/goldendict_exporter.py` (one-line fix + comment)
- `tests/tools/test_goldendict_exporter.py` (new, 4 tests)

### Verification commands
```bash
uv run ruff check --fix tools/goldendict_exporter.py tests/tools/test_goldendict_exporter.py
uv run ruff format tools/goldendict_exporter.py tests/tools/test_goldendict_exporter.py
uv run pyright tools/goldendict_exporter.py tests/tools/test_goldendict_exporter.py
uv run pytest tests/tools/test_goldendict_exporter.py -v
uv run pytest tests/
```

### Next action
User: please run an export with `include_slob=True` and confirm stderr is clean of `no such file or directory: …/pyglossary/tmp`. Then run `/kamma:3-review` (fresh session recommended).
