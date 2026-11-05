# Review fixes for thread 20261105_contrib_x_fixes

**Written for:** the agent "dpd contributor server 17". Follow it literally. The thread's spec is `spec.md` and its plan is `plan.md` in this folder; read the TL;DR in `spec.md` first.

**Source:** an independent review of the finished thread (2026-11-05). The review found no defect in the thread's own changes. It found two things to fix and some plan notes to correct. Everything below was verified by running code; the evidence is given so you can re-check it.

## Rules (all of them apply)

1. Work from `<repo root>` (the folder that holds `gui2/`, `tests/`, `scripts/`).
2. Do NOT run any `git` command. No stage, commit, stash, restore, reset, checkout or push. The owner commits. Other sessions share this working tree.
3. Do not write to GitHub. Never edit `.env` or `.ini` files.
4. Re-read a file from disk right before you edit it. `tests/scripts/server_contrib/test_maintenance_window.py` was changed on disk by another session while the reviewer was editing it. Edit nothing from memory.
5. Test first. For each fix: write the test, run it, see it FAIL for the reason named below, paste the failing line under the task in `plan.md`, then change the code, then see it pass.
6. After you edit a file run, in this order: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, then pyright, then the tests. Pyright: `uv run pyright <file>` for files under `scripts/`; `uv run pyright --project /dev/null <file>` for files under `tests/` and `gui2/` (plain pyright analyses nothing there).
7. Comments in code explain WHY, never WHAT. Do not touch existing comments. Type hints everywhere, modern forms (`list[str]`, `X | None`). Use `pathlib.Path`.
8. Do not run `scripts/server_contrib/ensure_translation_db.py` itself: on a machine without the database it starts an 807 MB download.
9. If something you read differs from this file, stop that fix, write what you saw under the task, and tell the owner.
10. Chat replies to the owner are plain English with no file paths or code names.

## Fix 1: the maintenance log loses its format after `pyglossary` is imported (Major)

### What is wrong
- Two tests fail in the full suite and pass alone: `tests/scripts/server_contrib/test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason` and `::TestTranslationDb::test_a_failure_is_logged_and_the_window_goes_on`. Both get `problems: 0` instead of `problems: 1`.
- Cause (proven): importing `pyglossary` calls `logging.setLoggerClass(pyglossary.logger.Logger)`. That class overrides `addHandler` so that it runs `hdlr.setFormatter(<its own formatter>)` right after adding the handler. Its format is `[ERROR] message`.
- `_make_logger` in `scripts/server_contrib/maintenance_window.py` sets the formatter BEFORE `logger.addHandler(handler)`. So the formatter is replaced at once, the log lines read `[ERROR] boom`, and `_write_status` (which looks for the substring `" ERROR "` with spaces) counts nothing.
- Who imports `pyglossary`: `tools/goldendict_exporter.py`, hence `tests/tools/test_goldendict_exporter.py` and `tests/exporter`. Collecting those tests is enough to trigger it.
- Production is not affected: the window never imports `pyglossary` (checked: `'pyglossary' in sys.modules` is `False` after importing the window module). This is also the most likely explanation of the original flaky failure in `spec.md` item 12 (it failed once in a full run and passed alone).
- Reproduce in 21 seconds (it collects the whole suite and runs only the two tests): `uv run pytest tests -k "test_status_file_reports_a_failure_and_its_reason or test_a_failure_is_logged_and_the_window_goes_on" -q -p no:cacheprovider`. Expected BEFORE the fix: `2 failed, 2976 deselected` (the deselected number may differ a little).

### Step 1.1: write the test (it must fail first)
In `tests/scripts/server_contrib/test_maintenance_window.py`:
- Add `import logging` to the imports (keep them sorted: it goes between `import json` and `import sqlite3`) and add `from scripts.server_contrib import maintenance_window` after `import pytest`'s blank line, before the line `from scripts.server_contrib.contrib_reconcile import ...`. Add the imports in the same edit as the test, so ruff does not remove them as unused.
- Add at the END of the file:

```python
class _FormatSwappingLogger(logging.Logger):
    """Behaves like pyglossary's logger class: adding a handler replaces its
    formatter."""

    def addHandler(self, hdlr: logging.Handler) -> None:
        super().addHandler(hdlr)
        hdlr.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))


class TestLogFormat:
    def test_the_format_survives_a_logger_class_that_swaps_formatters(
        self, tmp_path: Path
    ):
        previous = logging.getLoggerClass()
        logging.setLoggerClass(_FormatSwappingLogger)
        try:
            log = maintenance_window._make_logger(tmp_path / "logs")
            log.error("boom")
        finally:
            logging.setLoggerClass(previous)

        text = next((tmp_path / "logs").glob("maintenance_*.log")).read_text(
            encoding="utf-8"
        )

        assert " ERROR boom" in text
```

- Run: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py -q -p no:cacheprovider -k TestLogFormat`
- Expected now: FAILS with `AssertionError: assert ' ERROR boom' in '[ERROR] boom\n'`. Paste that line under task 16.1 in `plan.md`. If it passes, the test is wrong: stop and tell the owner.

### Step 1.2: fix the code
In `scripts/server_contrib/maintenance_window.py`, function `_make_logger`. Find exactly:

```python
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
```

Replace with:

```python
    handler = logging.FileHandler(log_path, encoding="utf-8")
    logger.addHandler(handler)
    # After addHandler, not before: pyglossary (imported by some tests) installs
    # a logger class whose addHandler replaces the handler's formatter.
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.propagate = False
```

Change nothing else in the function.

### Step 1.3: verify
- `uv run ruff check --fix scripts/server_contrib/maintenance_window.py tests/scripts/server_contrib/test_maintenance_window.py && uv run ruff format scripts/server_contrib/maintenance_window.py tests/scripts/server_contrib/test_maintenance_window.py`
- `uv run pyright scripts/server_contrib/maintenance_window.py | tail -1` (expect 0 errors)
- `uv run pyright --project /dev/null tests/scripts/server_contrib/test_maintenance_window.py | tail -1`. This file shows "X is not accessed" hints for stub parameters; they are pre-existing and are not errors. Make sure you add no NEW `error` lines. If the count is unclear, compare with the count before your edit (run the command once before you start).
- `uv run pytest tests/scripts/server_contrib -q -p no:cacheprovider` (all pass)
- The real proof: run the 21-second reproduction command above again. Expected now: `2 passed` (the two tests now pass even though the whole suite is collected, `pyglossary` included).

## Fix 2: a half-finished download blocks the translation database forever (Major)

### What is wrong
- `resources/tipitaka_translation_db/download_and_unzip_db.py`, function `ensure_zip_exists`, skips the download when the zip file exists (line ~48) and writes the download straight to the final zip path (line ~72). If the download dies part-way (network drop, kill), a broken zip stays on disk.
- Every later night the nightly window runs `scripts/server_contrib/ensure_translation_db.py`; the downloader skips the download (the zip "exists"), the unzip fails with a bad-zip error, the database never arrives, and the window logs `translation db missing` for ever, until someone deletes the zip by hand.
- That file lives in a separate repository (a submodule), so fix it in OUR script instead: when the database is still missing after the first try, delete the zip and try once more.

### Step 2.1: write the tests (they must fail first)
Edit `tests/scripts/server_contrib/test_ensure_translation_db.py`.
- Replace the `_Paths` class with:

```python
class _Paths:
    def __init__(self, path: Path, zip_path: Path | None = None) -> None:
        self.tipitaka_translation_db_path = path
        self.tipitaka_translation_db_tarball = zip_path or path.with_suffix(".db.zip")
```

- Keep the three existing tests as they are (they build `_Paths(db)` and still work).
- Add at the END of the file:

```python
def test_a_broken_zip_is_deleted_and_the_download_is_tried_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    zip_path = tmp_path / "translations.db.zip"
    zip_path.write_bytes(b"half a download")
    zip_present_at_each_call: list[bool] = []

    def fake_ensure() -> None:
        zip_present_at_each_call.append(zip_path.exists())
        if not zip_path.exists():
            db.write_bytes(b"x")

    monkeypatch.setattr(ensure_translation_db, "ensure_db_exists", fake_ensure)
    monkeypatch.setattr(
        ensure_translation_db, "ProjectPaths", lambda: _Paths(db, zip_path)
    )

    assert ensure_translation_db.main() == 0
    assert zip_present_at_each_call == [True, False]


def test_the_zip_is_kept_when_the_database_arrived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    db.write_bytes(b"x")
    zip_path = tmp_path / "translations.db.zip"
    zip_path.write_bytes(b"a good zip")
    calls: list[int] = []
    monkeypatch.setattr(
        ensure_translation_db, "ensure_db_exists", lambda: calls.append(1)
    )
    monkeypatch.setattr(
        ensure_translation_db, "ProjectPaths", lambda: _Paths(db, zip_path)
    )

    assert ensure_translation_db.main() == 0
    assert zip_path.exists()
    assert len(calls) == 1


def test_it_gives_up_after_one_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    calls: list[int] = []
    monkeypatch.setattr(
        ensure_translation_db, "ensure_db_exists", lambda: calls.append(1)
    )
    monkeypatch.setattr(ensure_translation_db, "ProjectPaths", lambda: _Paths(db))

    assert ensure_translation_db.main() == 1
    assert len(calls) == 2
```

- Run: `uv run pytest tests/scripts/server_contrib/test_ensure_translation_db.py -q -p no:cacheprovider`
- Expected now: `test_a_broken_zip_is_deleted_and_the_download_is_tried_again` FAILS (`assert [True] == [True, False]`, only one call is made today) and `test_it_gives_up_after_one_retry` FAILS (`assert 1 == 2`). `test_the_zip_is_kept_when_the_database_arrived` PASSES already: it guards against deleting a good zip, and must still pass after the fix. Paste one failing line under task 16.2.

### Step 2.2: fix the script
Replace the whole content of `scripts/server_contrib/ensure_translation_db.py` with:

```python
"""Make sure the Tipitaka translation database is on this machine.

Run by the nightly window. `ensure_db_exists` only prints when the download
fails, so the exit code is decided here: 0 when the file exists, 1 when not."""

import sys

from tools.paths import ProjectPaths
from tools.tipitaka_db import ensure_db_exists


def main() -> int:
    paths = ProjectPaths()
    ensure_db_exists()
    if not paths.tipitaka_translation_db_path.exists():
        # A download that died part-way leaves a broken zip, and the downloader
        # skips a zip that exists, so the database would never arrive.
        paths.tipitaka_translation_db_tarball.unlink(missing_ok=True)
        ensure_db_exists()
    return 0 if paths.tipitaka_translation_db_path.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Step 2.3: verify
- `uv run ruff check --fix scripts/server_contrib/ensure_translation_db.py tests/scripts/server_contrib/test_ensure_translation_db.py && uv run ruff format scripts/server_contrib/ensure_translation_db.py tests/scripts/server_contrib/test_ensure_translation_db.py`
- `uv run pyright scripts/server_contrib/ensure_translation_db.py | tail -1` (0 errors)
- `uv run pyright --project /dev/null tests/scripts/server_contrib/test_ensure_translation_db.py | tail -1`
- `uv run pytest tests/scripts/server_contrib/test_ensure_translation_db.py -q -p no:cacheprovider` (6 passed)

## Fix 3: correct the plan and the spec (text only)

Edit `kamma/threads/20261105_contrib_x_fixes/plan.md` and `spec.md`. Re-read each before editing.
1. Task 4.1 is `[~]`. Change the marker to `[x]`. The sweep ran; its result is already written under 4.6 (empty).
2. Task 14.2: replace the text from `CAUSE (from the failing run's tmp folder` to the end of that task with the corrected cause: `CAUSE FOUND in the review: importing pyglossary (tests/tools/test_goldendict_exporter.py, tests/exporter) installs a logger class whose addHandler replaces the handler's formatter; _make_logger set the formatter before addHandler. Production never imports pyglossary. Fixed in task 16.1 (formatter set after addHandler, regression test added).` Change the marker to `[x]`.
3. Task 14.3: append `Note: the two runs did not reproduce it because they never import pyglossary; see 14.2.`
4. Task 15.1: append the new result line after the fix (from task 16.4).
5. Add this at the end of the plan, as a new phase, and tick each task when done (write the failing and passing result lines under each):

```
## Phase 7: review fixes (see review_fixes.md)

- [ ] 16.1 Fix 1: log formatter set after addHandler, with a regression test.
- [ ] 16.2 Fix 2: ensure_translation_db deletes a broken zip and retries once, with tests.
- [ ] 16.3 Plan and spec notes corrected (tasks 4.1, 14.2, 14.3, 15.1).
- [ ] 16.4 Whole suite, type check, lint, graph update.
```

6. In `spec.md`, item 12 (`### 12. The flaky maintenance test`), add one line at its end: `Cause found 2026-11-05: importing pyglossary changes the logger class for the whole process and its addHandler replaces the handler's formatter; _make_logger now sets the formatter after addHandler. See plan task 16.1.`

## Task 16.4: final checks
1. `uv run pytest tests/ -q -p no:cacheprovider 2>&1 | tail -15`. Expected: 0 failed. (Before the fix: `2 failed, 2964 passed, 12 deselected`. The new tests add 4 passes.) Write the result line under 16.4 and under 15.1. If anything fails, show the owner the failing names; do not weaken a test.
2. `just typecheck 2>&1 | tail -8`. Expected: `0 errors`.
3. `uv run ruff check scripts/server_contrib/maintenance_window.py scripts/server_contrib/ensure_translation_db.py tests/scripts/server_contrib/test_maintenance_window.py tests/scripts/server_contrib/test_ensure_translation_db.py`. Expected: `All checks passed!`
4. `graphify update .` (run it once; it can take minutes). Then prune only when there are two or more snapshots: `[ "$(ls -d graphify-out/20* | wc -l)" -ge 2 ] && ls -d graphify-out/20* | sort | head -n -1 | xargs rm -rf`. Never delete `.graphifyignore`.
5. In `plan.md` task 15.4 add these to the lists: modified `scripts/server_contrib/maintenance_window.py` is already there, `tests/scripts/server_contrib/test_maintenance_window.py` is already there; add `kamma/threads/20261105_contrib_x_fixes/review_fixes.md` to the thread files, and make sure `scripts/server_contrib/ensure_translation_db.py` and `tests/scripts/server_contrib/test_ensure_translation_db.py` stay listed under New.

## Not part of this work (do not do these)
- `justfile` line 163 runs `flet run gui2/main.py -d`, which does not reach `run_app()`, so the dev-reload path does not make the preview folder. Desktop dev only; the owner knows. Leave it.
- No changes to the `resources/tipitaka_translation_db` submodule (separate repository).
- No server commands. The server one-off is already listed in plan task 15.5.

## Report back
When done, tell the owner in plain English: what you fixed, the two test result lines (the 21-second reproduction and the whole suite), and anything that did not match this file. Do not commit.
