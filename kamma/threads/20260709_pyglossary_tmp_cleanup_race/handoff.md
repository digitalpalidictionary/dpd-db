# Handoff: pyglossary cacheDir/tmp cleanup race

## Thread
- **ID:** 20260709_pyglossary_tmp_cleanup_race
- **Objective:** Eliminate the spurious `no such file or directory: …/pyglossary/tmp` stderr error that fires when `export_to_goldendict_with_pyglossary` runs with `include_slob=True`.

## The problem

Two `Glossary` instances are created in the same export: glos-outer in `export_to_goldendict_with_pyglossary`, glos-inner inside `write_to_slob`. Both call `add_css`/`add_js`/`add_fonts`/`add_data` — which call `newDataEntry()` — *before* `write()`. At that point `_tmpDataDir` is empty, so `newDataEntry` (`glossary_v2.py:628-639`) falls back to the shared `cacheDir/tmp`, creates it, and adds it to that glossary's `_cleanupPathList`.

Both glossaries end up with the *same* `cacheDir/tmp` path in their separate `_cleanupPathList` sets. glos-inner's `cleanup()` rmtrees it first (succeeds). glos-outer's `cleanup()` runs second, finds the dir gone, and hits the `else` branch (`glossary_v2.py:231`):

```python
log.error(f"no such file or directory: {cleanupPath}")
```

Exports succeed. It's log noise only.

## The solution (hypothesis — needs proving)

Add one line to `create_glossary()` in `tools/goldendict_exporter.py`, right after `Glossary(...)` construction:

```python
_ = glos.tmpDataDir
```

`tmpDataDir` is a public read-only property (`glossary_v2.py:551-553`) that lazily calls `_setTmpDataDir(self._filename)`. Since `_filename` is empty at creation, it substitutes `uuid1().hex`, producing `cacheDir/<uuid>_res` — a unique per-glossary dir. Once `_tmpDataDir` is set, `newDataEntry` takes the `if self._tmpDataDir:` branch (`:628`) and writes to the per-glossary dir instead of the shared `cacheDir/tmp`. Two glossaries → two distinct tmp dirs → no shared path → no double-rmtree race.

`_setTmpDataDir` also calls `self._cleanupPathList.add(self._tmpDataDir)` (`:682`), so each per-glossary dir is cleaned up by its own `cleanup()`.

## What the next agent must verify

1. **Prove the hypothesis by execution.** Apply the one-line fix, run an export with `include_slob=True`, and confirm the `no such file or directory` error is gone from stderr.
2. **Confirm `newDataEntry` takes the per-glossary branch.** Add a debug print (or use icecream) inside or after `create_glossary` to print `glos.tmpDataDir` and confirm it's `cacheDir/<uuid>_res`, not `cacheDir/tmp`. Confirm that `cacheDir/tmp` is never created during the export.
3. **Confirm nothing else uses `cacheDir/tmp`.** The slob writer uses `workdir=cacheDir` for `slob.Writer` (`plugins/aard2_slob/writer.py:97`), but that's slob's own temp managed by `slobWriter.finalize()`, not pyglossary's `_cleanupPathList`. Verify no stderr noise from that either.
4. **Write a regression test.** Two glossaries created via `create_glossary` must have different `tmpDataDir` values. See `plan.md` Phase 2.
5. **Run the pre-commit gate.** `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright`, `uv run pytest` on the changed file and related tests.

## Alternatives considered (and why they're inferior)

| Option | Verdict |
|---|---|
| Reuse parent glossary (vendor copy does this) | Works, eliminates race at source, but larger refactor. Good fallback if the one-line fix fails. |
| Per-glossary `_tmpDataDir` private write | Works, but touches private attr. The `glos.tmpDataDir` public property achieves the same thing. |
| Drop inner cleanup, rely on outer ("cleanup once at end") | Fixes symptom for current call graph only. Standalone `write_to_slob` would leak. Fragile. |
| Recreate `cacheDir/tmp` after inner cleanup (original handoff proposal) | Works, robust, but perpetually recreates a directory purely to keep a log quiet. Symptom patch. |

## Key files

- `tools/goldendict_exporter.py` — `create_glossary()` (~line 140), `write_to_slob()` (line 367), `export_to_goldendict_with_pyglossary()` (line 410)
- `.venv/lib/python3.13/site-packages/pyglossary/glossary_v2.py` — lines 214-232 (cleanup), 551-553 (tmpDataDir property), 628-639 (newDataEntry fallback), 665-682 (_setTmpDataDir)
- `.venv/lib/python3.13/site-packages/pyglossary/plugins/aard2_slob/writer.py` — line 97 (slob workdir=cacheDir)
- `resources/other-dictionaries/vendor/dpd_tools/goldendict_exporter.py` — vendored copy that reuses the parent glossary (no race)

## pyglossary version

5.4.1 (pinned in the project venv)
