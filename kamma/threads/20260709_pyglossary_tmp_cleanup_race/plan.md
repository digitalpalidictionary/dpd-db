# Plan: pyglossary cacheDir/tmp cleanup race in write_to_slob

## Architecture Decisions

1. **Fix location: `create_glossary()` in `tools/goldendict_exporter.py`** — this is the single entry point for all glossary creation (both Stardict and slob paths). Putting the fix here covers both export paths and is the smallest diff.

2. **Mechanism: `glos.tmpDataDir` property access** — forces `_setTmpDataDir` to run before any `newDataEntry` call, giving each glossary its own `cacheDir/<uuid>_res` dir. Public API, no private attribute access, no recreate hack.

3. **Not reusing the parent glossary** — the vendored copy does this, but it's a larger refactor. The one-line fix preserves the current architecture and is proven unnecessary only if the fix fails verification.

4. **Regression test** — a unit test that captures stderr during a slob export + outer cleanup and asserts no `no such file or directory` line appears. This guards against pyglossary upgrades silently reintroducing the race.

---

## Phase 1: Implement the fix

- [ ] Add `glos.tmpDataDir` access to `create_glossary()`
  - File: `tools/goldendict_exporter.py`, function `create_glossary` (line ~140)
  - After the `Glossary(...)` constructor and before `pr.yes("ok")`, add:
    ```python
    # Force a per-glossary tmp dir now, before any newDataEntry call.
    # Without this, newDataEntry falls back to the shared cacheDir/tmp,
    # and two glossaries race on cleanup (rmtree → "no such file" error).
    _ = glos.tmpDataDir
    ```
  - → verify: `uv run pyright tools/goldendict_exporter.py` passes, `uv run ruff check tools/goldendict_exporter.py` passes

- [ ] Confirm no type or lint errors
  - `_ = glos.tmpDataDir` is a property access for its side effect (triggers `_setTmpDataDir`). The `_` discard is F841-exempt in ruff (intentionally-unused-variable). No `# noqa` needed.
  - → verify: `uv run ruff check --fix tools/goldendict_exporter.py` and `uv run ruff format tools/goldendict_exporter.py` pass, `uv run pyright tools/goldendict_exporter.py` passes

## Phase 2: Regression test

- [ ] Create test file `tests/tools/test_goldendict_exporter.py`
  - Test that `create_glossary()` returns a Glossary with a non-empty `tmpDataDir` (confirms the fix is active).
  - Test that two separately-created glossaries have *different* `tmpDataDir` values (confirms no shared path).
  - If feasible without full export machinery: test that `write_to_slob` + outer `cleanup()` produces no `no such file or directory` on stderr. If full export is too heavy for a unit test, the `tmpDataDir` uniqueness test is sufficient as a regression guard.
  - → verify: `uv run pytest tests/tools/test_goldendict_exporter.py -v` passes

## Phase 3: Verify end-to-end

- [ ] Run the smoke gate
  - `uv run pytest tests/` — full test suite passes (or no new failures vs baseline)
  - → verify: no new failures

- [ ] Manual verification (user)
  - Run an export with `include_slob=True` and confirm no `no such file or directory` line on stderr.
  - → verify: stderr is clean of the error

## Phase 4: Finalize

- [ ] Review and finalize via kamma flow
  - → verify: `review.md` written, thread archived
