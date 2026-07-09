# Spec: pyglossary cacheDir/tmp cleanup race in write_to_slob

## Overview

When `export_to_goldendict_with_pyglossary` runs with `include_slob=True`, two `Glossary` instances are created — one in `export_to_goldendict_with_pyglossary` (glos-outer) and one inside `write_to_slob` (glos-inner). Both glossaries' `newDataEntry()` calls fall back to the shared `cacheDir/tmp` directory (because `_tmpDataDir` is empty until `write()` runs, and `add_css`/`add_js`/`add_fonts`/`add_data` all call `newDataEntry` *before* `write()`). Both glossaries add that same `cacheDir/tmp` path to their separate `_cleanupPathList` sets. When glos-inner's `cleanup()` rmtrees the dir first, glos-outer's `cleanup()` finds it missing and logs a spurious error:

```
no such file or directory: /home/runner/.cache/pyglossary/tmp
```

Exports succeed — this is log noise, not a correctness bug.

## What it should do

After the fix, running `export_to_goldendict_with_pyglossary(..., include_slob=True)` must produce no `no such file or directory` error on stderr. Each glossary must clean up its own tmp dir without colliding with the other.

## Root cause (verified against pyglossary 5.4.1)

- `glossary_v2.py:628-639` — `newDataEntry` falls back to `join(cacheDir, "tmp")` when `self._tmpDataDir` is empty, creates the dir, and adds it to `_cleanupPathList`.
- `glossary_v2.py:665-682` — `_setTmpDataDir` sets a per-glossary `cacheDir/<basename>_res` dir, but is only called inside `write()` / read paths — *after* `newDataEntry` has already used the shared fallback.
- `glossary_v2.py:214-232` — `cleanup()` does `rmtree(cleanupPath)` if `isdir`, else `log.error("no such file or directory: ...")`.
- `glossary_v2.py:551-553` — `tmpDataDir` is a public read-only property that lazily calls `_setTmpDataDir(self._filename)`. Since `_filename` is empty at glossary creation time, it substitutes `uuid1().hex`, producing a unique `cacheDir/<uuid>_res` dir per glossary.
- `newDataEntry` (`:628`) reads the raw `self._tmpDataDir` attribute, not the property — so the property must be accessed *before* any `newDataEntry` call.

## Proposed fix

Add one line to `create_glossary()` in `tools/goldendict_exporter.py`:

```python
_ = glos.tmpDataDir
```

This forces a per-glossary `cacheDir/<uuid>_res` tmp dir to be created immediately at glossary creation time, before any `newDataEntry` call. Two glossaries → two distinct tmp dirs → no shared path on either `_cleanupPathList` → the double-rmtree race disappears.

Note: this is a property access for its side effect (triggering `_setTmpDataDir`). The `_ =` discard signals intent — the value is irrelevant, the side effect is the point. Ruff treats `_` as intentionally unused (F841-exempt), so no `# noqa` needed. This is the standard Python idiom for "call this for side effects only."

**Why this is preferred over alternatives:**
- **Root cause vs. symptom:** the alternative of recreating `cacheDir/tmp` after inner cleanup (`Path(cacheDir, "tmp").mkdir(...)`) patches the symptom — the two glossaries still collide on the same path, we just paper over the second rmtree. This fix prevents the shared-path collision entirely by giving each glossary its own unique tmp dir.
- Public API only — no private attribute access (`_tmpDataDir`), no `# type: ignore`.
- Robust to standalone `write_to_slob` calls (unlike "cleanup once at the end" which relies on the outer glossary).
- No recreate-then-rmtree hack.
- The vendored copy (`resources/other-dictionaries/vendor/dpd_tools/goldendict_exporter.py`) reuses the parent glossary and has no race — confirming a separate-glossary-per-path pattern is sound, but the one-line `tmpDataDir` access is a smaller diff that preserves the current two-glossary architecture.

## Assumptions & uncertainties

- **Assumption:** accessing `glos.tmpDataDir` before any `newDataEntry` call causes `newDataEntry` to take the `if self._tmpDataDir:` branch (`:628`), writing DataEntry files to the per-glossary dir instead of the shared `cacheDir/tmp`. Verified by reading the source — but **not yet proven by execution**.
- **Assumption:** the per-glossary `<uuid>_res` dir is properly cleaned up by `cleanup()` because `_setTmpDataDir` calls `self._cleanupPathList.add(self._tmpDataDir)` (`:682`). Verified by source.
- **Uncertainty:** whether any pyglossary internal calls `newDataEntry` during `write()` that might still hit the fallback if `_tmpDataDir` were somehow cleared. Not observed, but the verifying agent should confirm via a test run.
- **Uncertainty:** whether the slob writer (`plugins/aard2_slob/writer.py`) uses `cacheDir` as its own `workdir` (`:97`) in a way that could still collide. Source inspection shows slob manages its own temp via `slob.Writer.finalize()`, not via pyglossary's `_cleanupPathList` — but the verifying agent should confirm no stderr noise remains.

## Constraints

- Must use pyglossary 5.4.1 (currently pinned).
- Must not touch private attributes if a public API route exists.
- Must not break the vendored copy or any downstream exporter that calls `export_to_goldendict_with_pyglossary`.
- `create_glossary` is called by all export paths (Stardict + slob), so the fix affects both — this is desired (both paths had the latent race).

## How we'll know it's done

- `export_to_goldendict_with_pyglossary(..., include_slob=True)` produces no `no such file or directory` line on stderr.
- A regression test exists that asserts the outer `cleanup()` after `write_to_slob` emits no such error.
- `uv run pytest tests/tools/test_goldendict_exporter.py` passes.
- `uv run ruff check` and `uv run pyright` pass on the changed file.

## What's not included

- Fixing the unrelated "copy_dir goldenDict path" `no` message (separate issue).
- Refactoring `write_to_slob` to reuse the parent glossary (the vendor copy already does this; not needed if the one-line fix works).
- Upgrading pyglossary to a version that may have fixed this upstream.
