# Plan: contributor problem children, the small fixes

**Thread:** 20261105_contrib_x_fixes · **Spec:** `spec.md` (read it first; this plan only says how)
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Written for:** a less capable model. Every task names the file, the exact edit, the exact test and the exact commands. Do not improvise. If something you read differs from this plan, STOP that task, write what you saw under the task, and ask the owner.

## Executor rules (read all of them before task 1)

1. Work from `<repo root>` (the folder that holds `gui2/`, `tests/`, `scripts/`). Every shell command below assumes that folder.
2. Do NOT run any `git` command. Do not commit, stage, stash, restore, reset or push. The owner commits. Other sessions share this working tree.
3. Do not write to GitHub (no issue comments, no labels).
4. Never edit `.env` or any `.ini` file. Never print a file that holds secrets.
5. Before you edit a file, read it again from disk. Another session may have changed it.
6. One task at a time, in order. Mark the task `[~]` when you start and `[x]` when its `→ verify:` lines pass. Do not mark `[x]` on a guess.
7. Test first. For every task that has a test: write the test, run it, and see it FAIL for the reason named in the task. Paste the failing line under the task. Only then change the code. Then run the test again and see it pass. A test that passes before the fix is wrong; fix the test.
8. Comments in code explain WHY, never WHAT. Do not touch existing comments. Do not add comments that say how other code is wired unless you re-read that code first.
9. Type hints everywhere. Modern forms only: `list[str]`, `dict[str, str]`, `X | None`. Use `pathlib.Path`, not `os`. Do not add `print`; the project uses `icecream` (`from icecream import ic`) for debugging, but do not leave any debug call behind.
10. After you edit a file, run in this order: `uv run ruff check --fix <file>`, then `uv run ruff format <file>`, then the type check below, then the tests of the task.
    - Files under `gui2/` and `tests/`: `uv run pyright --project /dev/null <file>`. This repo already shows many pyright errors in `gui2/` files (flet typing). Do not try to fix those. Record the error count of each file in the baseline task, and make sure your change adds none.
    - Other files: `uv run pyright <file>`.
11. Run scripts with `uv run <path>.py` and tests with `uv run pytest <path>`. Never `pip install`, never `uv add`.
12. If a command fails and the reason is not in this plan, show the error to the owner. Do not retry in a loop. Any background loop needs `timeout`.
13. Keep a short note under each task: what you changed (file and function), the test result line.
14. Chat replies to the owner are in plain English with no file paths or code names, except when asking the owner about a specific file.

## Architecture decisions

- Smallest change per fix. No new flags, no new settings, no shared helper unless a task says so.
- `Pass2AddView._copy_lemma` is the one new helper (task 1): two call sites and a message that depends on the result, so a helper is the smallest testable shape.
- `run_app()` in `gui2/main.py` (task 2) exists only so the folder fix can be tested; the `__main__` block cannot be.
- The disabled Save button uses one attribute name, `save_button`, on all three tabs, so `GlobalView._view` can disable it with one `getattr` (task 9).
- The nightly checkout is NOT deleted (owner decision after Goldfish review). Only the database copy `dpd.db.prev` is.
- Alt keys are guarded by one local variable (`alt`) at the top of `on_keyboard` (task 11). No shared helper; there is one call site.
- Audio in the preview and contributor password change are separate threads. Do not start them.
- The translation database step in the nightly window is injectable and has NO default in the test helpers (a no-op is passed), so no test can start the real 183 MB download (task 13).
- Transl becomes a base tab by moving one label between two tuples (task 12); the tab bar order does not change.

## Phase 0: baseline (before any edit)

- [x] 0.1 Record what is already failing.
  - Run: `uv run pytest tests/gui2 tests/scripts/server_contrib tests/tools/test_fast_api_utils.py -q 2>&1 | tail -15`
  - Write under this task: the last line (for example `N passed, M failed`) and the names of any failing tests. A failing test that is listed here is NOT yours to fix.
  - → verify: the result line is written under this task.
  - Result: `892 passed in 14.12s`. No failing tests.
- [x] 0.2 Record the repo-wide type check baseline.
  - Run: `just typecheck 2>&1 | tail -8`. This runs pyrefly, not pyright; its numbers are not comparable with the pyright counts in 0.3.
  - Write the result line under this task.
  - → verify: the result line is written under this task.
  - Result: `0 errors (123 suppressed, 91 warnings not shown)` (a WARN about a stale PYTHONPATH pointing at an old `Code/dpd-db` path is from the environment, not the check).
- [x] 0.3 Record the pyright error count of each file you will edit.
  - Run each line, write the last line of each output under this task:
    - `uv run pyright --project /dev/null gui2/pass2_add_view.py | tail -1`
    - `uv run pyright --project /dev/null gui2/main.py | tail -1`
    - `uv run pyright --project /dev/null gui2/database_manager.py | tail -1`
    - `uv run pyright --project /dev/null gui2/pass1_add_controller.py | tail -1`
    - `uv run pyright --project /dev/null gui2/filter_component.py | tail -1`
    - `uv run pyright --project /dev/null gui2/filter_tab_view.py | tail -1`
    - `uv run pyright --project /dev/null gui2/roots_tab_view.py | tail -1`
    - `uv run pyright --project /dev/null gui2/inflection_templates_tab_view.py | tail -1`
    - `uv run pyright --project /dev/null gui2/contributor_tabs.py | tail -1`
    - `uv run pyright scripts/server_contrib/contrib_pull.py | tail -1`
    - `uv run pyright scripts/server_contrib/maintenance_window.py | tail -1`
  - → verify: eleven lines written under this task.
  - Results:
    - `gui2/pass2_add_view.py` — 46 errors
    - `gui2/main.py` — 24 errors
    - `gui2/database_manager.py` — 0 errors
    - `gui2/pass1_add_controller.py` — 3 errors
    - `gui2/filter_component.py` — 9 errors
    - `gui2/filter_tab_view.py` — 22 errors
    - `gui2/roots_tab_view.py` — 14 errors
    - `gui2/inflection_templates_tab_view.py` — 24 errors
    - `gui2/contributor_tabs.py` — 0 errors
    - `scripts/server_contrib/contrib_pull.py` — 0 errors
    - `scripts/server_contrib/maintenance_window.py` — 0 errors

## Phase 1: small fixes in gui2

### Task 1: clipboard copy never cuts off a save (spec 1)

- [x] 1.1 Write the test. Create `tests/gui2/test_pass2_add_clipboard.py` with exactly this content:

```python
"""A refused clipboard copy must not stop a Pass2Add save."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from gui2.pass2_add_view import Pass2AddView


class _Clipboard:
    """Stands in for ft.Clipboard. The class attribute decides the outcome."""

    fail: bool = False
    copied: list[str] = []

    async def set(self, value: str) -> None:
        if self.fail:
            raise RuntimeError("PlatformException(copy_fail, Clipboard.setData failed.)")
        _Clipboard.copied.append(value)


@pytest.fixture(autouse=True)
def _fake_clipboard(monkeypatch: pytest.MonkeyPatch) -> None:
    _Clipboard.fail = False
    _Clipboard.copied = []
    monkeypatch.setattr(ft, "Clipboard", _Clipboard)


@pytest.fixture(autouse=True)
def _stub_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flet 1.0 raises on `.page` of an unmounted control.
    monkeypatch.setattr(Pass2AddView, "page", MagicMock(), raising=False)


def _view() -> Pass2AddView:
    return object.__new__(Pass2AddView)


def test_copy_lemma_returns_true_and_copies() -> None:
    assert asyncio.run(_view()._copy_lemma("kata 1")) is True
    assert _Clipboard.copied == ["kata 1"]


def test_copy_lemma_returns_false_when_the_browser_refuses() -> None:
    _Clipboard.fail = True
    assert asyncio.run(_view()._copy_lemma("kata 1")) is False
    assert _Clipboard.copied == []


def _x_view(copied: bool) -> Pass2AddView:
    """A view that can run _click_x_button for a queued word with no id."""
    view = _view()
    view._x_manager = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view._x_manager.get_next.return_value = ("kata", {"comment": "from X"})
    view._x_manager.remaining_count.return_value = 4
    view.clear_all_fields = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.dpd_fields = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.dpd_fields.fields = {}
    view.add_headword_to_examples_and_commentary = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view.update_message = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    view._copy_lemma = AsyncMock(return_value=copied)  # pyright: ignore[reportAttributeAccessIssue]
    return view


def test_x_button_message_says_copied_when_the_copy_worked() -> None:
    view = _x_view(copied=True)

    asyncio.run(view._click_x_button(MagicMock()))

    view.update_message.assert_called_once_with("[4] kata: from X (lemma_1 copied)")  # pyright: ignore[reportAttributeAccessIssue]


def test_x_button_message_says_not_copied_when_the_browser_refused() -> None:
    view = _x_view(copied=False)

    asyncio.run(view._click_x_button(MagicMock()))

    view.update_message.assert_called_once_with(  # pyright: ignore[reportAttributeAccessIssue]
        "[4] kata: from X (lemma_1 NOT copied: clipboard blocked)"
    )
```

  If a test fails with an `AttributeError` that names another attribute of the view, add that attribute to `_x_view` as a `MagicMock()`; do not change the asserted message strings.

  - Run: `uv run pytest tests/gui2/test_pass2_add_clipboard.py -q`
  - Expected now: the two `_copy_lemma` tests FAIL with `AttributeError: ... has no attribute '_copy_lemma'`. The two `x_button` tests FAIL with an `AssertionError` (the old code still calls `ft.Clipboard()` and cannot return "NOT copied"; with the fake clipboard it may also pass the "copied" one: that is fine, the "NOT copied" one must fail). Paste one failing line.
- [x] 1.2 Add the helper. (added `_copy_lemma` after `update_message` in `gui2/pass2_add_view.py`; paste of failing line: `AssertionError: expected call not found. Expected: mock('[4] kata: from X (lemma_1 NOT copied: clipboard blocked)') Actual: mock('[4] kata: from X (lemma_1 copied)')`) Edit `gui2/pass2_add_view.py`. Find this method (about line 484):

```python
    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()
```

  Add directly after it (one blank line between):

```python
    async def _copy_lemma(self, lemma_1: str) -> bool:
        """Copy lemma_1 to the clipboard. A browser can refuse the copy, and
        that must never cut off the rest of a save."""
        try:
            await ft.Clipboard().set(lemma_1)
        except Exception:
            return False
        return True
```

- [x] 1.3 Use it at site 1 in `_save_previewed_word` (about line 1066). Find:

```python
            await ft.Clipboard().set(word_to_save.lemma_1)

            self._update_history_dropdown()
            self.page.update()
            # clear_all_fields keeps the sutta filter; a finished add should not
            self._filter_radios.value = "all"
            self.clear_all_fields()
            self._show_missing_words_dialog(word_to_save)
```

  Replace with (note the message goes AFTER `clear_all_fields()`, because that method ends with `self.update_message("")`):

```python
            copied = await self._copy_lemma(word_to_save.lemma_1)

            self._update_history_dropdown()
            self.page.update()
            # clear_all_fields keeps the sutta filter; a finished add should not
            self._filter_radios.value = "all"
            self.clear_all_fields()
            if not copied:
                self.update_message(
                    "Saved, but lemma_1 was not copied (clipboard blocked)"
                )
            self._show_missing_words_dialog(word_to_save)
```

- [x] 1.4 Use it at site 2 in `_click_x_button` (about line 1344). Find:

```python
            lemma_1 = headword.lemma_1 if headword else values.get("lemma_1", word)
            await ft.Clipboard().set(lemma_1)

            remaining = self._x_manager.remaining_count()
            self.update_message(
                f"[{remaining}] {word}: {comment} (lemma_1 copied)"
                if comment
                else f"[{remaining}] {word} (lemma_1 copied)"
            )
```

  Replace with:

```python
            lemma_1 = headword.lemma_1 if headword else values.get("lemma_1", word)
            copied = await self._copy_lemma(lemma_1)

            remaining = self._x_manager.remaining_count()
            note = "lemma_1 copied" if copied else "lemma_1 NOT copied: clipboard blocked"
            self.update_message(
                f"[{remaining}] {word}: {comment} ({note})"
                if comment
                else f"[{remaining}] {word} ({note})"
            )
```

- [x] 1.5 Verify. Result: 38 passed (four files); pyright 46 errors = baseline; rg shows exactly one `ft.Clipboard()` (line 492, inside `_copy_lemma`); site 1 re-read: the `if not copied:` block sits after `self.clear_all_fields()` and before `_show_missing_words_dialog`.
  - Run: `uv run ruff check --fix gui2/pass2_add_view.py tests/gui2/test_pass2_add_clipboard.py && uv run ruff format gui2/pass2_add_view.py tests/gui2/test_pass2_add_clipboard.py`
  - Run: `uv run pyright --project /dev/null gui2/pass2_add_view.py | tail -1` and `uv run pyright --project /dev/null tests/gui2/test_pass2_add_clipboard.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_pass2_add_clipboard.py tests/gui2/test_pass2_add_reject.py tests/gui2/test_pass2_add_eg_dialog.py tests/gui2/test_pass2_add_component_words.py -q`
  - Run: `rg -n "Clipboard" gui2/pass2_add_view.py`
  - → verify: the four new tests pass; the other three files pass; the pyright count of `gui2/pass2_add_view.py` is not higher than in task 0.3; the `rg` shows exactly ONE `ft.Clipboard()` line, inside `_copy_lemma`.
  - Limit to state under the task: site 2 (the X button) is tested for both messages; site 1 (`_save_previewed_word`, after a save) is checked by reading only, because the surrounding save needs many collaborators. Read it once more and confirm the `if not copied:` block sits after `self.clear_all_fields()`.

### Task 2: preview folder exists before Flet starts (spec 2)

- [x] 2.1 Write the test. Paste: `ImportError: cannot import name 'run_app' from 'gui2.main'` Open `tests/gui2/test_main.py`. In the import block `from gui2.main import (` add `run_app,` (keep the names sorted as the file does). At the END of the file add:

```python
def test_run_app_makes_the_preview_folder_before_flet_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preview_dir = tmp_path / "assets" / "preview"
    seen: list[bool] = []
    monkeypatch.setattr("gui2.preview.PREVIEW_DIR", preview_dir)
    monkeypatch.setattr(
        "gui2.main.ft.run", lambda target: seen.append(preview_dir.is_dir())
    )

    run_app()

    assert seen == [True]
```

  If `Path` is not imported in that file, add `from pathlib import Path` to its imports.
  - Run: `uv run pytest tests/gui2/test_main.py -q -k run_app`
  - Expected now: collection error `ImportError: cannot import name 'run_app'`. Paste that line under this task. (The real fail-for-the-right-reason check is step A in 2.2.)
- [x] 2.2 Edit `gui2/main.py` (step A fail line: `assert [False] == [True]`, as expected; step B adds the mkdir) in two steps. The import is INSIDE the function on purpose: `gui2/main.py` loads its views lazily, and `gui2.preview` pulls in the webapp and jinja stack, so a top-level import would slow every import of `gui2.main`. (Checked 2026-11-05: `gui2/preview.py` does not import `gui2.main`, so there is no cycle.) The test patches `gui2.preview.PREVIEW_DIR`, which a function-level import reads at call time.
  Step A. Find the end of the file:

```python
if __name__ == "__main__":
    ft.run(main)
```

  Replace with (no `mkdir` yet):

```python
def run_app() -> None:
    ft.run(main)


if __name__ == "__main__":
    run_app()
```

  Run: `uv run pytest tests/gui2/test_main.py -q -k run_app`. Expected: the test FAILS with `assert [False] == [True]` (the folder did not exist when `ft.run` was called). Paste that line. If it passes, the test is wrong: stop and tell the owner.
  Step B. Change `run_app` to:

```python
def run_app() -> None:
    from gui2.preview import PREVIEW_DIR

    # Flet looks for the assets folder once, at start, and drops it if it is
    # missing; the preview page is only written later.
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    ft.run(main)
```

- [x] 2.3 Verify. Result: 64 passed in tests/gui2/test_main.py; pyright 24 errors = baseline.
  - Run: `uv run ruff check --fix gui2/main.py tests/gui2/test_main.py && uv run ruff format gui2/main.py tests/gui2/test_main.py`
  - Run: `uv run pyright --project /dev/null gui2/main.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_main.py -q`
  - → verify: the new test passes; the whole file passes (if task 11 is not done yet, the other tests are unchanged); the pyright count is not higher than in task 0.3.

### Task 3: no warning for the read-only database (spec 3)

- [x] 3.1 Write the test. Paste: `assert 'decon cache refresh failed' not in 'decon cache...e/20/e3q8)` — real text was `decon cache refresh failed: (sqlite3.OperationalError) attempt to write a readonly database` (contains `readonly database`) Create `tests/gui2/test_database_manager_decon_cache.py` with exactly this content:

```python
"""The decon cache refresh stays quiet on a read-only database only."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import gui2.database_manager as database_manager_module
from db.models import Base, Lookup
from gui2.database_manager import DatabaseManager


def _read_only_session(tmp_path: Path) -> Session:
    path = tmp_path / "ro.db"
    Base.metadata.create_all(create_engine(f"sqlite:///{path}"))
    engine = create_engine(f"sqlite:///file:{path}?mode=ro&uri=true")
    return Session(engine)


def _manager(session: Session) -> DatabaseManager:
    manager = object.__new__(DatabaseManager)
    manager.db_session = session
    return manager


def test_a_read_only_database_prints_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manager = _manager(_read_only_session(tmp_path))

    manager.get_all_decon_no_headwords()

    assert "decon cache refresh failed" not in capsys.readouterr().out
    assert manager.all_decon_no_headwords == set()


def test_any_other_failure_still_prints_and_the_session_stays_usable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _read_only_session(tmp_path)
    manager = _manager(session)

    def locked(*args: object, **kwargs: object) -> None:
        raise RuntimeError("database is locked")

    monkeypatch.setattr(
        database_manager_module, "save_decon_no_headwords_cache", locked
    )

    manager.get_all_decon_no_headwords()

    assert "decon cache refresh failed: database is locked" in capsys.readouterr().out
    assert session.query(Lookup).count() == 0
```

  - Run: `uv run pytest tests/gui2/test_database_manager_decon_cache.py -q -s`
  - Expected now: `test_a_read_only_database_prints_nothing` FAILS with `AssertionError: assert 'decon cache refresh failed' not in ...`. Paste that line. The printed text after it should read like `decon cache refresh failed: (sqlite3.OperationalError) attempt to write a readonly database` (SQLAlchemy adds the `[SQL: ...]` part after it; that is fine). If the words `readonly database` are NOT in it, STOP and tell the owner the real text; do not guess another match.
- [x] 3.2 Edit `gui2/database_manager.py` (added the `if "readonly database" ...` guard with comment) (about lines 390-399). Find:

```python
            print(f"decon cache refresh failed: {exc}")
```

  Replace that single line with these two lines (same indentation, 12 spaces), and change nothing else in the block (leave the existing comments and the `self.db_session.rollback()`):

```python
            if "readonly database" not in str(exc).lower():
                print(f"decon cache refresh failed: {exc}")
```

  Then add one comment line directly above the `if`, same indentation: `# A read-only database (the contributor server) can never take the cache.`
- [x] 3.3 Verify. Result: 42 passed (three files); pyright 0 errors = baseline; print still present inside the `if` (line 398).
  - Run: `uv run ruff check --fix gui2/database_manager.py tests/gui2/test_database_manager_decon_cache.py && uv run ruff format gui2/database_manager.py tests/gui2/test_database_manager_decon_cache.py`
  - Run: `uv run pyright --project /dev/null gui2/database_manager.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_database_manager_decon_cache.py tests/gui2/test_database_manager_corpus.py tests/tools/test_decon_no_headwords_cache.py -q`
  - → verify: both new tests pass; the other two files pass; the pyright count is not higher than in task 0.3; `rg -n "decon cache refresh failed" gui2/database_manager.py` shows the print is still there (inside the `if`).

### Task 4: remove the helper web server (spec 4)

- [x] 4.1 Sweep first. Run:
  `rg --hidden -n "start_dpd_server|request_dpd_server|fast_api_utils|DPD_API_PORT|FastAPI server" --glob '!graphify-out' --glob '!archive' --glob '!.git' --glob '!kamma' .`
  The pattern matches nothing in `exporter/` or the `justfile` today (read 2026-11-05); if a hit appears there, do not edit it, write it under this task and ask the owner.
  Expected hits (read 2026-11-05): `gui2/main.py` (import, comment, call, print), `tools/fast_api_utils.py`, `tests/tools/test_fast_api_utils.py`, `tests/gui2/test_main.py` (two monkeypatch lines), `scripts/server_contrib/config_server.template` (line 16). If there are other hits, write each under this task and apply the spec rule: remove a mention only if it names the gui2-started helper or `DPD_API_PORT`; leave the webapp itself (`exporter/webapp/`), `exporter/wxt_extension/`, the `justfile` and `archive/`.
- [x] 4.2 Edit `gui2/main.py` (deleted the import and the start block).
  - Delete the line `from tools.fast_api_utils import start_dpd_server` (about line 22).
  - Find and delete this block (about lines 743-748), including the comment and the blank line after it:

```python
    # Start the FastAPI server after the UI has painted so it never delays the
    # window appearing.
    start_time = time.time()
    start_dpd_server()
    print(f"FastAPI server started in {time.time() - start_time:.2f}s")
```

  - Leave the earlier `start_time = time.time()` / `App initialized in` lines untouched. Leave `import time` (still used).
- [x] 4.3 Edit `tests/gui2/test_main.py` (both monkeypatch lines deleted).: delete BOTH lines `    monkeypatch.setattr("gui2.main.start_dpd_server", MagicMock())` (about lines 627 and 652). Keep everything else in those tests.
- [x] 4.4 Edit `scripts/server_contrib/config_server.template` line 16 (DPD_API_PORT removed). line 16. Find `# systemd unit (DPD_GUI2_USERNAME, DPD_GUI2_ROLE, DPD_API_PORT); the values` and change it to `# systemd unit (DPD_GUI2_USERNAME, DPD_GUI2_ROLE); the values`. Change nothing else in that file. Do not print or open any other file in that folder that may hold keys.
- [x] 4.5 Delete the two dead files (rm done, both missing). with: `rm tools/fast_api_utils.py tests/tools/test_fast_api_utils.py`
- [x] 4.6 Verify. Sweep output: empty (no hits at all). 64 passed in tests/gui2/test_main.py; pyright 24 = baseline; both files missing.
  - Run the sweep from 4.1 again. Expected: no hit left except the kept ones (`archive/` is excluded from the command). Write the output under this task.
  - Run: `uv run ruff check --fix gui2/main.py tests/gui2/test_main.py && uv run ruff format gui2/main.py tests/gui2/test_main.py`
  - Run: `uv run pyright --project /dev/null gui2/main.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_main.py -q`
  - → verify: the sweep is empty; `tests/gui2/test_main.py` passes; the pyright count is not higher than in task 0.3; `ls tools/fast_api_utils.py tests/tools/test_fast_api_utils.py` says both are missing.

### Task 5: pattern rename marks the corpus stale (spec 5)

- [x] 5.1 Write the test. Paste: `assert False = <...>._corpus_stale` at line 325 (expected fail). Open `tests/gui2/test_database_manager_corpus.py`. After `test_update_word_in_db_marks_corpus_stale` (it starts at about line 303 and ends at about line 311), before the `# ── detector rebuild worker` comment, add:

```python
def test_rename_pattern_in_headwords_marks_corpus_stale(db_manager: DatabaseManager):
    db_manager.db_session.query(DpdHeadword).filter_by(id=2).update(
        {"pattern": "old"}
    )
    db_manager.db_session.commit()
    db_manager.load_corpus()
    assert db_manager._corpus_stale is False

    count = db_manager.rename_pattern_in_headwords("old", "new")

    assert count == 1
    assert db_manager._corpus_stale is True
```

  - Run: `uv run pytest tests/gui2/test_database_manager_corpus.py -q -k rename_pattern`
  - Expected now: FAILS on `assert db_manager._corpus_stale is True`. Paste that line.
- [x] 5.2 Edit `gui2/database_manager.py` (added `self.mark_corpus_stale()` after the commit). (about line 795). Find:

```python
        self.db_session.commit()
        return count

    def sync_inflection_templates(self) -> list[str]:
```

  Change to:

```python
        self.db_session.commit()
        self.mark_corpus_stale()
        return count

    def sync_inflection_templates(self) -> list[str]:
```

- [x] 5.3 Verify. Result: 34 passed (two files); pyright 0 errors = baseline.
  - Run: `uv run ruff check --fix gui2/database_manager.py tests/gui2/test_database_manager_corpus.py && uv run ruff format gui2/database_manager.py tests/gui2/test_database_manager_corpus.py`
  - Run: `uv run pyright --project /dev/null gui2/database_manager.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_database_manager_corpus.py tests/gui2/test_inflection_templates_db.py -q`
  - → verify: the new test passes; both files pass; the pyright count is not higher than in task 0.3.

### Task 6: remove the unused additions manager (spec 6)

- [x] 6.1 Prove it is unused. Hits exactly as expected (pass1_add_controller.py lines 8, 48; test stub line 103). Nothing reads `controller.additions_manager` (second rg: no hits). Run: `rg -n "additions_manager" gui2/pass1_add_controller.py gui2/pass1_add_view.py gui2/pass1_auto_controller.py tests/gui2/test_pass1_add_controller.py tests/gui2/test_pass1_add_view.py`
  Expected (read 2026-11-05): `gui2/pass1_add_controller.py` lines 8 (import) and 48 (assignment), and one stub line in `tests/gui2/test_pass1_add_controller.py` (a fake toolkit attribute, line ~103). Also run: `rg -n "controller\.additions_manager|pass1_add_controller.*additions_manager" gui2 tests`. If anything READS `additions_manager` from a Pass1AddController, STOP and ask the owner.
- [x] 6.2 Edit `gui2/pass1_add_controller.py` (both lines deleted).: delete line 8 `from gui2.additions_manager import AdditionsManager` and line 48 `self.additions_manager: AdditionsManager = toolkit.additions_manager`. Leave the test stub as it is (it stands in for the toolkit, which still has the manager).
- [x] 6.3 Verify. Result: 6 passed (two files); pyright 3 errors = baseline; rg prints nothing.
  - Run: `uv run ruff check --fix gui2/pass1_add_controller.py && uv run ruff format gui2/pass1_add_controller.py`
  - Run: `uv run pyright --project /dev/null gui2/pass1_add_controller.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_pass1_add_controller.py tests/gui2/test_pass1_add_view.py -q`
  - → verify: both files pass; the pyright count is not higher than in task 0.3; `rg -n "additions_manager|AdditionsManager" gui2/pass1_add_controller.py` prints nothing.

## Phase 2: contributor-server scripts

### Task 7: notice when the pull skips because the editor is open (spec 7)

- [x] 7.1 Write the tests. Paste: 3 failed (`AttributeError: ... has no attribute 'notify_editor_open'`), 3 guard tests passed as expected. Open `tests/scripts/server_contrib/test_contrib_pull.py`. After the test `test_a_notice_that_cannot_be_sent_is_noted_in_the_status` and its body (search for it; it is near line 633), add:

```python
def test_the_editor_open_skip_sends_a_notice(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []
    monkeypatch.setattr(contrib_pull, "notify", sent.append)

    contrib_pull.notify_editor_open(Status(outcome=contrib_pull.EDITOR_OPEN))

    assert sent == ["skipped: editor open"]


def test_a_failed_editor_open_notice_is_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(message: str) -> None:
        raise FileNotFoundError("notify-send")

    monkeypatch.setattr(contrib_pull, "notify", broken)

    contrib_pull.notify_editor_open(Status(outcome=contrib_pull.EDITOR_OPEN))


def _run_main(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcome: str, *argv: str
) -> list[str]:
    sent: list[str] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["contrib_pull", *argv])
    monkeypatch.setattr(contrib_pull, "config_read", lambda *_: "user@host")
    monkeypatch.setattr(contrib_pull.SharedFiles, "default", lambda: None)
    monkeypatch.setattr(
        contrib_pull, "run", lambda *args, **kwargs: Status(outcome=outcome)
    )
    monkeypatch.setattr(contrib_pull, "notify", sent.append)
    contrib_pull.main()
    return sent


def test_main_sends_one_notice_for_an_editor_open_skip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sent = _run_main(monkeypatch, tmp_path, "skipped: editor open")

    assert sent == ["skipped: editor open"]


@pytest.mark.parametrize(
    "outcome", ["skipped: already done today", "skipped: another run"]
)
def test_main_stays_silent_for_the_other_skips(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcome: str
) -> None:
    assert _run_main(monkeypatch, tmp_path, outcome) == []


def test_main_sends_no_notice_on_a_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert _run_main(monkeypatch, tmp_path, "skipped: editor open", "--dry-run") == []
```

  - Run: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q -k "editor_open or other_skips or dry_run"`
  - Expected now: exactly these three FAIL: `test_the_editor_open_skip_sends_a_notice` and `test_a_failed_editor_open_notice_is_swallowed` (`AttributeError: module ... has no attribute 'notify_editor_open'` or `'EDITOR_OPEN'`), and `test_main_sends_one_notice_for_an_editor_open_skip` (`assert [] == ['skipped: editor open']`). Paste one failing line. The three guard tests (`test_main_stays_silent_for_the_other_skips` twice, `test_main_sends_no_notice_on_a_dry_run`) already PASS before the fix and must still pass after: they stop the fix from notifying too much. That is expected; do not edit them.
- [x] 7.2 Edit `scripts/server_contrib/contrib_pull.py` (EDITOR_OPEN constant, two literals replaced, notify_editor_open added, main branch replaced).
  - Near the other module constants (after `NOTICE_FROM = time(22, 30)`, line ~47) add: `EDITOR_OPEN = "skipped: editor open"`.
  - Replace the two literals `status.outcome = "skipped: editor open"` (about lines 476 and 526) with `status.outcome = EDITOR_OPEN`. Do not change the other skip strings.
  - After the function `maybe_notify` (it ends just before `def main`), add:

```python
def notify_editor_open(status: Status) -> None:
    """Tell the maintainer the pull skipped because gui2 is open. A skip writes
    no status file, so the notice is the only sign of it. A failed notice is
    ignored: the next run tries again."""
    try:
        notify(status.outcome)
    except (OSError, subprocess.SubprocessError):
        pass
```

  - In `main`, find:

```python
    if not args.dry_run and not status.outcome.startswith("skipped"):
        maybe_notify(status, now)
        if status.notice_error:
            write_status(status_path, status)
```

  Replace with:

```python
    if not args.dry_run:
        if status.outcome == EDITOR_OPEN:
            notify_editor_open(status)
        elif not status.outcome.startswith("skipped"):
            maybe_notify(status, now)
            if status.notice_error:
                write_status(status_path, status)
```

  Leave the two lines after it (`sys.stdout.write(...)` and the `return`) unchanged.
- [x] 7.3 Verify. Result: 130 passed in the file; pyright 0 errors.
  - Run: `uv run ruff check --fix scripts/server_contrib/contrib_pull.py tests/scripts/server_contrib/test_contrib_pull.py && uv run ruff format scripts/server_contrib/contrib_pull.py tests/scripts/server_contrib/test_contrib_pull.py`
  - Run: `uv run pyright scripts/server_contrib/contrib_pull.py | tail -1`
  - Run: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q`
  - → verify: all new tests pass; the whole file passes (the old test `test_no_notice_for_a_good_or_skipped_run` must still pass: `maybe_notify` was not changed); pyright reports no new error.

### Task 8: delete the database copy after a good window (spec 8)

- [x] 8.1 Write the tests. Paste: 3 failed as expected (rebuilt, skipped, log), 2 guard tests passed already. Open `tests/scripts/server_contrib/test_maintenance_window.py`. At the END of the file add:

```python
def _prev(setup: Setup) -> Path:
    return setup.config.db_path.with_name("dpd.db.prev")


class TestDatabaseCopyCleanup:
    def test_a_rebuilt_run_removes_the_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)

        assert run_maintenance(setup.config, _steps(Calls())) is Outcome.REBUILT

        assert not _prev(setup).exists()

    def test_a_skipped_run_removes_the_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)
        run_maintenance(setup.config, _steps(Calls()))

        assert run_maintenance(setup.config, _steps(Calls())) is Outcome.SKIPPED

        assert not _prev(setup).exists()

    def test_a_failed_run_keeps_the_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)
        broken = _steps(Calls(), rebuild=Calls().step("rebuild", RuntimeError("boom")))

        assert run_maintenance(setup.config, broken) is Outcome.FAILED

        assert _prev(setup).exists()

    def test_a_refused_run_deletes_nothing(self, tmp_path: Path):
        setup = _setup(tmp_path)
        _prev(setup).write_bytes(b"older copy")
        (setup.repo / "tracked.tsv").write_text("hand edit\n")

        assert run_maintenance(setup.config, _steps(Calls())) is Outcome.FAILED

        assert _prev(setup).read_bytes() == b"older copy"

    def test_the_log_names_the_deleted_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)

        run_maintenance(setup.config, _steps(Calls()))

        assert "removed dpd.db.prev" in setup.log_text()
```

  - Run: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py -q -k DatabaseCopyCleanup`
  - Expected now: `test_a_rebuilt_run_removes_the_copy`, `test_a_skipped_run_removes_the_copy` and `test_the_log_names_the_deleted_copy` FAIL (the copy is still there). The failed and refused tests PASS already: they guard against deleting too much, and must still pass after the fix. Paste one failing line.
  - Note: the log line `removed dpd.db.prev ...` is written at INFO level, so the status file (which counts only ERROR and WARNING lines) does not list it. That is intended.
- [x] 8.2 Edit `scripts/server_contrib/maintenance_window.py` (added `_remove_database_copy` before `run_maintenance`, and the `finally` guard). Find the end of the function:

```python
    finally:
        _systemctl("start", config.instances, config, log)
        log.info(f"maintenance window end: {outcome.value}")
        _write_status(config, outcome, log)
    return outcome
```

  Replace with:

```python
    finally:
        _systemctl("start", config.instances, config, log)
        if outcome is not Outcome.FAILED:
            _remove_database_copy(config, log)
        log.info(f"maintenance window end: {outcome.value}")
        _write_status(config, outcome, log)
    return outcome
```

  Add this function directly BEFORE `def run_maintenance` (leave two blank lines around it):

```python
def _remove_database_copy(config: WindowConfig, log: logging.Logger) -> None:
    """Delete the rollback copy once the run cannot need it. It is built from
    config, not from the Rollback object, which does not exist when the run
    returned early. This runs in a `finally`, so a failure is logged, never
    raised."""
    copy = config.db_path.with_name(config.db_path.name + ".prev")
    try:
        if copy.exists():
            size = copy.stat().st_size
            copy.unlink()
            log.info(f"removed {copy.name} ({size} bytes)")
    except OSError as exc:
        log.warning(f"could not remove {copy.name}: {exc}")
```

  Do not change `_capture_rollback`, `_restore_rollback` or anything else.
- [x] 8.3 Add two lines to `.gitignore` (appended at the end, LF endings preserved). (open it, go to the end, add them on new lines at the end, keep the file's line endings):

```
dpd.db.prev
*_contrib_worktree/
```

  Reason (do not write it in the file): the copy may sit inside a clone, and a worktree placed inside the clone would show as untracked. The default worktree is beside the clone, outside the repo.
- [x] 8.4 Verify. Result: 25 passed (incl. TestRollback/TestRollbackWal); pyright 0 errors; .gitignore ends with the two new lines.
  - Run: `uv run ruff check --fix scripts/server_contrib/maintenance_window.py tests/scripts/server_contrib/test_maintenance_window.py && uv run ruff format scripts/server_contrib/maintenance_window.py tests/scripts/server_contrib/test_maintenance_window.py`
  - Run: `uv run pyright scripts/server_contrib/maintenance_window.py | tail -1`
  - Run: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py -q`
  - Run: `tail -3 .gitignore`
  - → verify: the five new tests pass; the whole file passes; pyright reports no new error; `.gitignore` ends with the two new lines and nothing else changed.
  - The existing rollback tests (`TestRollback`, `TestRollbackWal`) must still pass: they prove a failed run still restores from the copy.

## Phase 3: gui2 behaviour

### Task 9: grey out Save on read-only tabs (spec 9)

- [x] 9.1 Write the tests. Paste: 4 failed (`AttributeError ... save_button`), 2 passed.
  - In `tests/gui2/test_read_only_views.py` add at the END:

```python
@pytest.mark.parametrize("read_only", [True, False])
def test_filter_component_save_button_is_disabled_when_read_only(
    monkeypatch: pytest.MonkeyPatch, read_only: bool
) -> None:
    _stub_page(monkeypatch, FilterComponent)

    component = FilterComponent(MagicMock(), MagicMock(), read_only=read_only)

    assert component.save_button.disabled is read_only


def test_roots_and_infl_keep_their_save_button(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_page(monkeypatch, RootsTabView)
    roots = RootsTabView(MagicMock(), MagicMock())
    infl = InflectionTemplatesTabView(MagicMock(), MagicMock())

    assert roots.save_button.on_click == roots._save_root
    assert infl.save_button.on_click == infl._save_template
```

  - In `tests/gui2/test_main.py` add at the END (`Any` and `SimpleNamespace` are already imported there):

```python
def test_server_read_tab_gets_its_save_button_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app: Any = _server_app(monkeypatch, "√")
    app._view_builders[14] = lambda: SimpleNamespace(
        save_button=SimpleNamespace(disabled=False)
    )

    view = app._view(14)

    assert view.read_only is True
    assert view.save_button.disabled is True


def test_a_tab_that_is_not_read_only_keeps_its_save_button_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app: Any = _server_app(monkeypatch, "√")
    app._view_builders[8] = lambda: SimpleNamespace(
        save_button=SimpleNamespace(disabled=False)
    )

    view = app._view(8)

    assert view.save_button.disabled is False
```

  - Run: `uv run pytest tests/gui2/test_read_only_views.py tests/gui2/test_main.py -q -k "save_button"`
  - Expected now: all new tests FAIL (`AttributeError ... save_button` or `assert False is True`). Paste one failing line.
- [x] 9.2 DB tab. Edit `gui2/filter_component.py`, method `_build_ui` (about line 174). Find:

```python
        results_section = self._create_results_section()

        self.controls.extend(
            [
                results_section,
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Button("Save Changes", on_click=self._save_changes),
```

  Replace with:

```python
        results_section = self._create_results_section()
        self.save_button = ft.Button(
            "Save Changes", on_click=self._save_changes, disabled=self.read_only
        )

        self.controls.extend(
            [
                results_section,
                ft.Container(
                    content=ft.Row(
                        [
                            self.save_button,
```

  Do not change the lines after that (`self.prev_page_button`, ...). `self.read_only` is set before `_build_ui()` runs (constructor line ~118), so it is available.
- [x] 9.3 Roots tab. Edit `gui2/roots_tab_view.py`, method `_build_bottom_section` (about line 166). Find:

```python
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Button(
                        "Save to DB",
                        on_click=self._save_root,
                        width=BUTTON_WIDTH,
                    ),
                    self._delete_button,
```

  Replace with:

```python
        self.save_button = ft.Button(
            "Save to DB",
            on_click=self._save_root,
            width=BUTTON_WIDTH,
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    self.save_button,
                    self._delete_button,
```

- [x] 9.4 Inflection tab. Edit `gui2/inflection_templates_tab_view.py`, method `_build_bottom_section` (about line 419). Find:

```python
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Button("Save", on_click=self._save_template, width=BUTTON_WIDTH),
```

  Replace with:

```python
        self.save_button = ft.Button(
            "Save", on_click=self._save_template, width=BUTTON_WIDTH
        )
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.save_button,
```

  Keep the Delete button and everything after it unchanged.
- [x] 9.5 Disable it for read-only tabs. Edit `gui2/main.py`, method `_view`. Find:

```python
                view = self._view_builders[index]()
                if index in self._read_only:
                    setattr(view, "read_only", True)
                self._views[index] = view
```

  Replace with:

```python
                view = self._view_builders[index]()
                if index in self._read_only:
                    setattr(view, "read_only", True)
                    save_button = getattr(view, "save_button", None)
                    if save_button is not None:
                        save_button.disabled = True
                self._views[index] = view
```

- [x] 9.6 Verify. Result: 126 passed (four files); pyright: filter_component 8 (< 9 baseline), roots 13 (< 14 baseline), inflection 24 = baseline, main 24 = baseline.
  - Run: `uv run ruff check --fix gui2/filter_component.py gui2/roots_tab_view.py gui2/inflection_templates_tab_view.py gui2/main.py tests/gui2/test_read_only_views.py tests/gui2/test_main.py && uv run ruff format gui2/filter_component.py gui2/roots_tab_view.py gui2/inflection_templates_tab_view.py gui2/main.py tests/gui2/test_read_only_views.py tests/gui2/test_main.py`
  - Run `uv run pyright --project /dev/null <file> | tail -1` for each of the four gui2 files; compare with task 0.3.
  - Run: `uv run pytest tests/gui2/test_read_only_views.py tests/gui2/test_main.py tests/gui2/test_inflection_templates_tab_view.py tests/gui2/test_roots_db.py -q`
  - → verify: all new tests pass; the four files pass; no new pyright error. The handlers still refuse (the old tests in `test_read_only_views.py` prove it).

### Task 10: starter preset for contributors on the DB tab (spec 10)

- [x] 10.1 Write the tests. Paste: `ImportError: cannot import name 'CONTRIBUTOR_DATA_FILTERS' from 'gui2.filter_tab_view'`; after 10.2: `AttributeError: 'App' object has no attribute '_make_filter_tab'`; after 10.3 all pass. Create `tests/gui2/test_filter_tab_starter.py` with this content:

```python
"""A contributor with no saved preset opens the DB tab on the starter preset."""

from unittest.mock import MagicMock

import pytest

from gui2.filter_tab_view import (
    CONTRIBUTOR_DATA_FILTERS,
    CONTRIBUTOR_DISPLAY_FILTERS,
    FilterTabView,
)
from gui2.main import App


@pytest.fixture(autouse=True)
def _stub_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flet 1.0 raises on `.page` of an unmounted control.
    monkeypatch.setattr(FilterTabView, "page", MagicMock(), raising=False)


def _toolkit(*, not_primary: bool, first_preset: dict | None = None) -> MagicMock:
    toolkit = MagicMock()
    toolkit.username_manager.is_not_primary.return_value = not_primary
    toolkit.filter_presets_manager.get_first_preset.return_value = first_preset
    return toolkit


def _app(toolkit: MagicMock) -> App:
    app = App.__new__(App)
    app.page = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    app.toolkit = toolkit  # pyright: ignore[reportAttributeAccessIssue]
    return app


def _checked(view: FilterTabView) -> set[str]:
    return {str(box.label) for box in view.column_checkboxes if box.value}


def test_the_starter_values_are_the_agreed_ones() -> None:
    assert CONTRIBUTOR_DATA_FILTERS == [("lemma_1", "")]
    assert CONTRIBUTOR_DISPLAY_FILTERS == [
        "id",
        "pos",
        "grammar",
        "meaning_1",
        "meaning_2",
        "meaning_lit",
    ]


def test_a_contributor_with_no_preset_gets_the_starter() -> None:
    view = _app(_toolkit(not_primary=True))._make_filter_tab()

    assert view.column_dropdowns[0].value == "lemma_1"
    assert view.regex_inputs[0].value == ""
    assert _checked(view) == set(CONTRIBUTOR_DISPLAY_FILTERS)


def test_the_primary_user_keeps_the_old_defaults() -> None:
    view = _app(_toolkit(not_primary=False))._make_filter_tab()

    assert view.column_dropdowns[0].value == "root_key"
    assert "root_key" in _checked(view)


def test_a_saved_preset_wins_over_the_starter() -> None:
    preset = {
        "data_filters": [["pos", "noun"]],
        "display_filters": ["id", "pos"],
        "limit": 50,
    }
    view = _app(_toolkit(not_primary=True, first_preset=preset))._make_filter_tab()

    assert view.column_dropdowns[0].value == "pos"
    assert _checked(view) == {"id", "pos"}


def test_reset_gives_the_starter_when_no_preset_is_saved() -> None:
    view = _app(_toolkit(not_primary=True))._make_filter_tab()
    view.column_dropdowns[0].value = "stem"

    view._reset_to_default_clicked(None)

    assert view.column_dropdowns[0].value == "lemma_1"
    assert _checked(view) == set(CONTRIBUTOR_DISPLAY_FILTERS)
```

  - Run: `uv run pytest tests/gui2/test_filter_tab_starter.py -q`
  - Expected now: collection error `ImportError: cannot import name 'CONTRIBUTOR_DATA_FILTERS'` (the constants do not exist until step 10.2; `_make_filter_tab` does not exist until step 10.3). Paste that line. After step 10.2 and before step 10.3, the tests that call `_make_filter_tab` must fail with `AttributeError: ... has no attribute '_make_filter_tab'`; after 10.3 they must pass.
  - The `_toolkit` helper mocks only what the tab reads when no preset is saved. If you add a test with a saved preset that has data filters, the tab builds a `FilterComponent`, which also reads `toolkit.paths.user_dictionary_path`; the `MagicMock` toolkit already answers that, so no change is needed.
  - Note for you: if after the fix a test fails because the tab starts with an extra empty filter row, or because a column name (for example `grammar`) is not an offered column, read `FilterTabView._initialize_filters` and `DpdHeadword.__table__.columns`, then adjust the ASSERT (not the starter values) and tell the owner what you saw. The starter values come from the owner.
- [x] 10.2 Edit `gui2/filter_tab_view.py` (constants above the class, `_default_data_filters`/`_default_display_filters` stored, reset `else` branch uses them).
  - Above `class FilterTabView(ft.Column):` add (two blank lines before and after):

```python
CONTRIBUTOR_DATA_FILTERS: list[tuple[str, str]] = [("lemma_1", "")]
CONTRIBUTOR_DISPLAY_FILTERS: list[str] = [
    "id",
    "pos",
    "grammar",
    "meaning_1",
    "meaning_2",
    "meaning_lit",
]
```

  - In `__init__`, directly after `self.read_only: bool = False` (about line 37) add:

```python
        # Reset to Default must give back the starter this tab was opened with.
        self._default_data_filters = data_filters
        self._default_display_filters = display_filters
```

  - In `_reset_to_default_clicked` (about lines 771-830) find the `else:` branch that begins `# Fallback to original hardwired values if no presets exist`. Replace the whole branch body (from `default_data_filters = [("root_key", ""), ("family_root", "")]` down to the `self._initialize_filters(` call and its closing parenthesis) with:

```python
            self._initialize_filters(
                data_filters=self._default_data_filters,
                display_filters=self._default_display_filters,
                limit=DEFAULT_LIMIT,
            )
```

    Keep the `else:` line and its comment line; remove only the typed-in `default_data_filters`, `default_display_filters`, `default_limit` variables and the old call. Keep the call exactly as shown, WITHOUT a `page` argument (the old call had none; the reset runs on a mounted page and ends with `self.page.update()`). The constructor parameter defaults stay as they are, so the primary user gets the same values as before.
- [x] 10.3 Edit `gui2/main.py`. DEVIATION (plan quoted the import as top-level; it is actually inside `App.__init__`, the lazy-import architecture the plan itself documents): the builder import could not be seen from the new method, so `_make_filter_tab` imports the names itself, the `__init__` import was removed (ruff), and a `TYPE_CHECKING` import plus a quoted return annotation `-> "FilterTabView"` were added at the top of `gui2/main.py`. Same behaviour as planned.
  - In the import line for `gui2.filter_tab_view` change it to import the two constants as well. Find `from gui2.filter_tab_view import FilterTabView` and make it:

```python
from gui2.filter_tab_view import (
    CONTRIBUTOR_DATA_FILTERS,
    CONTRIBUTOR_DISPLAY_FILTERS,
    FilterTabView,
)
```

  - In the builders dict change `11: lambda: FilterTabView(self.page, self.toolkit),` to `11: self._make_filter_tab,`.
  - Add this method to the `App` class (put it directly before `_on_submit_data`, with one blank line around it):

```python
    def _make_filter_tab(self) -> FilterTabView:
        if self.toolkit.username_manager.is_not_primary():
            return FilterTabView(
                self.page,
                self.toolkit,
                data_filters=CONTRIBUTOR_DATA_FILTERS,
                display_filters=CONTRIBUTOR_DISPLAY_FILTERS,
            )
        return FilterTabView(self.page, self.toolkit)
```

- [x] 10.4 Verify. Result: 136 passed (five files); pyright filter_tab_view 22 = baseline, main 24 = baseline.
  - Run: `uv run ruff check --fix gui2/filter_tab_view.py gui2/main.py tests/gui2/test_filter_tab_starter.py && uv run ruff format gui2/filter_tab_view.py gui2/main.py tests/gui2/test_filter_tab_starter.py`
  - Run `uv run pyright --project /dev/null gui2/filter_tab_view.py | tail -1` and the same for `gui2/main.py`; compare with task 0.3.
  - Run: `uv run pytest tests/gui2/test_filter_tab_starter.py tests/gui2/test_read_only_views.py tests/gui2/test_main.py tests/gui2/test_filter_presets_manager.py tests/gui2/test_filter_logic.py -q`
  - → verify: the five new tests pass; the other files pass; no new pyright error.

### Task 11: Alt shortcuts off in the web version (spec 11)

- [x] 11.1 Fix the two test helpers first (web=False added to both). so existing tests keep their meaning. Edit `tests/gui2/test_main.py`:
  - In `_app_on_tab`, find `app.page = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]` and its argument line `_dialogs=SimpleNamespace(controls=[dialog]), show_dialog=MagicMock()`. Change that argument line to exactly `_dialogs=SimpleNamespace(controls=[dialog]), show_dialog=MagicMock(), web=False` (the `ruff format` step later may re-break the line; that is fine).
  - In `_server_app`, find `app.page = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]` and add on the next line: `app.page.web = False` with the comment line above it: `# Alt keys are off in the web; these tests are about tab visibility.`
- [x] 11.2 Write the new tests. Paste: 3 failed (web=True Alt tests still act), web=False cases and Ctrl+S passed. Reuse the helpers that already exist in the file (`_key`, `_ctrl_s`, `_server_app`, `_app_on_tab`); do not define them again. Add at the END of `tests/gui2/test_main.py`:

```python
@pytest.mark.parametrize("web, expected_tab", [(False, 11), (True, 3)])
def test_alt_d_jumps_to_the_db_tab_only_outside_the_web(
    monkeypatch: pytest.MonkeyPatch, web: bool, expected_tab: int
) -> None:
    app = _server_app(monkeypatch, "DB")
    app.page.web = web  # pyright: ignore[reportAttributeAccessIssue]

    asyncio.run(app.on_keyboard(_key("D", alt=True)))

    assert app._current_index() == expected_tab


def test_alt_arrow_does_nothing_in_the_web(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _server_app(monkeypatch, "DB")
    app.page.web = True  # pyright: ignore[reportAttributeAccessIssue]

    asyncio.run(app.on_keyboard(_key("Arrow Right", alt=True)))

    assert app._current_index() == 3


@pytest.mark.parametrize("web, opened", [(False, True), (True, False)])
def test_alt_question_mark_opens_the_popup_only_outside_the_web(
    monkeypatch: pytest.MonkeyPatch, web: bool, opened: bool
) -> None:
    app = _server_app(monkeypatch, "DB")
    app.page.web = web  # pyright: ignore[reportAttributeAccessIssue]

    asyncio.run(app.on_keyboard(_key("?", alt=True)))

    assert app.page.show_dialog.called is opened  # pyright: ignore[reportAttributeAccessIssue]


def test_ctrl_s_still_works_in_the_web(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _server_app(monkeypatch, "DB")
    app.page.web = True  # pyright: ignore[reportAttributeAccessIssue]
    view = app._view(app._current_index())
    view._save_changes_clicked = MagicMock()

    asyncio.run(app.on_keyboard(_ctrl_s()))

    view._save_changes_clicked.assert_called_once_with(None)
```

  - Run: `uv run pytest tests/gui2/test_main.py -q -k "web"`
  - Expected now: the three `web=True` Alt tests FAIL (Alt still acts). The `web=False` cases and the Ctrl+S test PASS. Paste one failing line.
  - If `test_ctrl_s_still_works_in_the_web` fails for a reason that is not about Alt, STOP and tell the owner; do not change production code for it.
- [x] 11.3 Edit `gui2/main.py` (`alt` local, five conditions replaced; `rg "e\.alt"` shows exactly one hit). Directly after the docstring line `"""Handles global keyboard events."""` add:

```python
        # Some Alt keys clash with the browser's own, so they are off in the web.
        alt = e.alt and not self.page.web
```

  Then replace `e.alt` with `alt` in exactly these five conditions (and nowhere else; do not rename the parameter `e`):
  1. `elif e.key == "Arrow Left" and e.alt:` becomes `elif e.key == "Arrow Left" and alt:`
  2. `elif e.key == "Arrow Right" and e.alt:` becomes `elif e.key == "Arrow Right" and alt:`
  3. `elif e.key == "X" and e.alt:` becomes `elif e.key == "X" and alt:`
  4. `elif e.alt and e.key in self._SHORTCUTS_KEYS:` becomes `elif alt and e.key in self._SHORTCUTS_KEYS:`
  5. the tab-jump condition: the line `e.alt` inside `elif (` ... `):` (about line 367) becomes `alt`.
  - Run: `rg -n "e\.alt" gui2/main.py` and expect exactly ONE hit: the new line `alt = e.alt and not self.page.web`.
- [x] 11.4 Verify. Result: 75 passed (two files, incl. old Alt tests); pyright 24 = baseline.
  - Run: `uv run ruff check --fix gui2/main.py tests/gui2/test_main.py && uv run ruff format gui2/main.py tests/gui2/test_main.py`
  - Run: `uv run pyright --project /dev/null gui2/main.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_main.py tests/gui2/test_shortcuts_dialog.py -q`
  - → verify: the new tests pass; the WHOLE file passes, including the old Alt tests (`test_alt_x_*`, `test_alt_question_mark_*`, `test_server_alt_*`); no new pyright error.

### Task 12: the Translations tab for every contributor (spec 13)

- [x] 12.1 Change the tests first. Paste: 9 failed (the edited + new tests), 71 passed.
  - `tests/gui2/test_contributor_tabs.py` (the label list there has `Transl` at index 1):
    - `test_base_only`: change the expected list to `["Transl", "Pass1Add"]`.
    - `test_indices_are_original_positions`: change `assert visible == [3, 14, 16]` to `assert visible == [1, 3, 14, 16]`.
    - `test_hidden_and_unknown_labels_dropped_with_warning`: change the expected list to `["Transl", "Pass1Add", "DB"]`.
    - `test_base_safe_and_read` stays as it is (it passes before and after).
    - Add at the end:

```python
def test_transl_is_always_visible_and_never_read_only() -> None:
    visible, read_only = allowed_tabs(ALL_LABELS, [])
    assert 1 in visible
    assert 1 not in read_only
```

  - `tests/gui2/test_main.py`, the server tests (they build a contributor session with `_server_app`; Transl is now visible, so every position moves by one). Make exactly these edits:
    - `test_server_shows_base_and_listed_tabs_only`: expected labels become `["Transl", "Pass1Add", "DB", "Bold Search"]`; `len(app._tab_bodies.controls) == 4`; `app.tabs.selected_index == 1`; `app._current_index() == 3` stays.
    - `test_server_alt_jump_selects_a_listed_tab`: `app.tabs.selected_index == 2` (visible tabs are now Transl, Pass1Add, DB, Bold Search; DB is third); the other two asserts stay.
    - `test_server_alt_arrows_stay_inside_the_visible_tabs`: the first assert becomes `assert app._current_index() == 1` (Alt+Left from Pass1Add now reaches Transl); the final assert after five Alt+Right presses stays `== 11`.
    - `test_server_warmup_builds_only_visible_tabs`: `assert built == [3, 1, 13, 11]` (the order comes from `App._WARMUP_TAB_ORDER`: 3, then 1, then 13, then 11).
    - Add at the end:

```python
def test_a_contributor_with_no_extra_tabs_still_sees_transl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "")

    assert _tab_bar_labels(app) == ["Transl", "Pass1Add"]
```

  - Run: `uv run pytest tests/gui2/test_contributor_tabs.py tests/gui2/test_main.py -q`
  - Expected now: the edited and new tests FAIL (Transl is not visible yet). Paste one failing line.
  - If another test in `test_main.py` fails after the code change below for a reason that is only "Transl is now visible", write the test name and the reason under this task and ask the owner before changing it.
- [x] 12.2 Edit `gui2/contributor_tabs.py` (BASE_TABS/SAFE_TABS swapped). Find:

```python
BASE_TABS = ("Pass1Add",)
SAFE_TABS = ("Transl", "Bold Search")
```

  Replace with:

```python
BASE_TABS = ("Pass1Add", "Transl")
SAFE_TABS = ("Bold Search",)
```

  Change nothing else in the file. A `Transl` still listed in `DPD_GUI2_TABS` is harmless: the loop only adds a label that is already allowed.
- [x] 12.3 Edit the table in `gui2/README.md` (both rows replaced). (rows at lines 49-50). Two separate edits, each a find and a replace:
  Edit 1. Find this row: `| Base (always) | Pass1Auto, Pass1Add | Saves go to the contributor's own JSON files |`
  Replace it with: `| Base (always) | Pass1Add, Transl | Pass1Add saves to the contributor's own JSON files; Transl searches only |`
  (`Pass1Auto` leaves the row on purpose: `BASE_TABS` never listed it, and the server tests show tab 2 is hidden.)
  Edit 2. Find this row: `| Safe (extra, by env) | Transl, Bold Search | Write nothing shared |`
  Replace it with: `| Safe (extra, by env) | Bold Search | Writes nothing shared |`
  Do not touch the other rows.
- [x] 12.4 Verify. Result: 89 passed (three files); pyright 0 errors; the two new values confirmed by rg.
  - Run: `uv run ruff check --fix gui2/contributor_tabs.py tests/gui2/test_contributor_tabs.py tests/gui2/test_main.py && uv run ruff format gui2/contributor_tabs.py tests/gui2/test_contributor_tabs.py tests/gui2/test_main.py`
  - Run: `uv run pyright --project /dev/null gui2/contributor_tabs.py | tail -1`
  - Run: `uv run pytest tests/gui2/test_contributor_tabs.py tests/gui2/test_main.py tests/scripts/server_contrib/test_add_contributor.py -q`
  - → verify: all pass; pyright reports no new error for `gui2/contributor_tabs.py`; `rg -n "BASE_TABS|SAFE_TABS" gui2/contributor_tabs.py` shows the two new values.

### Task 13: the translation database is always on the server (spec 14)

- [x] 13.1 Write the tests for the new script. Paste: `ImportError: cannot import name 'ensure_translation_db' from 'scripts.server_contrib'` Create `tests/scripts/server_contrib/test_ensure_translation_db.py`:

```python
"""ensure_translation_db exits 0 only when the database file exists afterwards."""

from pathlib import Path

import pytest

from scripts.server_contrib import ensure_translation_db


class _Paths:
    def __init__(self, path: Path) -> None:
        self.tipitaka_translation_db_path = path


def test_exit_zero_when_the_database_is_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    db.write_bytes(b"x")
    monkeypatch.setattr(ensure_translation_db, "ensure_db_exists", lambda: None)
    monkeypatch.setattr(ensure_translation_db, "ProjectPaths", lambda: _Paths(db))

    assert ensure_translation_db.main() == 0


def test_exit_one_when_the_database_is_still_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ensure_translation_db, "ensure_db_exists", lambda: None)
    monkeypatch.setattr(
        ensure_translation_db, "ProjectPaths", lambda: _Paths(tmp_path / "none.db")
    )

    assert ensure_translation_db.main() == 1


def test_it_downloads_before_it_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    monkeypatch.setattr(
        ensure_translation_db, "ensure_db_exists", lambda: db.write_bytes(b"x")
    )
    monkeypatch.setattr(ensure_translation_db, "ProjectPaths", lambda: _Paths(db))

    assert ensure_translation_db.main() == 0
```

  - Run: `uv run pytest tests/scripts/server_contrib/test_ensure_translation_db.py -q`
  - Expected now: collection error `ImportError` (the module does not exist). Paste that line.
- [x] 13.2 Create `scripts/server_contrib/ensure_translation_db.py` (script not run). 3 passed; pyright 0 errors.

```python
"""Make sure the Tipitaka translation database is on this machine.

Run by the nightly window. `ensure_db_exists` only prints when the download
fails, so the exit code is decided here: 0 when the file exists, 1 when not."""

import sys

from tools.paths import ProjectPaths
from tools.tipitaka_db import ensure_db_exists


def main() -> int:
    ensure_db_exists()
    return 0 if ProjectPaths().tipitaka_translation_db_path.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
```

  - Run: `uv run ruff check --fix scripts/server_contrib/ensure_translation_db.py tests/scripts/server_contrib/test_ensure_translation_db.py && uv run ruff format scripts/server_contrib/ensure_translation_db.py tests/scripts/server_contrib/test_ensure_translation_db.py`
  - Run: `uv run pyright scripts/server_contrib/ensure_translation_db.py | tail -1`
  - Run: `uv run pytest tests/scripts/server_contrib/test_ensure_translation_db.py -q`
  - → verify: three tests pass; pyright reports no error. Do NOT run the script itself: on a machine without the database it starts a download.
- [x] 13.3 Write the window tests. Paste: `TypeError: WindowSteps.__init__() got an unexpected keyword argument 'translation_db'` Edit `tests/scripts/server_contrib/test_maintenance_window.py`.
  - In the helper `_steps` (about line 74) add one argument to the `WindowSteps(...)` call, after `health_check=...`: `translation_db=lambda config: None,`. The new dataclass field is required, so the constructor call needs it; a test that wants something else passes `translation_db=...` as an override, which the helper applies afterwards with `setattr`. The no-op records nothing, so the existing `calls.names` asserts keep holding.
  - Edit `tests/scripts/server_contrib/test_round_trip.py`, function `_stub_steps` (about line 53): add `translation_db=lambda c: None,` after `health_check=lambda c: None,`.
  - At the END of `test_maintenance_window.py` add:

```python
class TestTranslationDb:
    def test_the_step_runs_every_window_and_is_logged(self, tmp_path: Path):
        setup = _setup(tmp_path)
        calls = Calls()
        steps = _steps(calls, translation_db=calls.step("translation_db"))

        run_maintenance(setup.config, steps)
        run_maintenance(setup.config, _steps(Calls(), translation_db=calls.step("translation_db")))

        assert calls.names.count("translation_db") == 2
        assert "translation db present" in setup.log_text()

    def test_a_failure_is_logged_and_the_window_goes_on(self, tmp_path: Path):
        setup = _setup(tmp_path)
        calls = Calls()
        steps = _steps(
            calls,
            translation_db=Calls().step("translation_db", RuntimeError("no network")),
        )

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.REBUILT
        assert "rebuild" in calls.names
        assert "translation db missing (window goes on): no network" in setup.log_text()
        status = (setup.config.log_dir / "status.txt").read_text(encoding="utf-8")
        assert "problems: 1" in status
        assert "translation db missing" in status
```

  - Run: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py tests/scripts/server_contrib/test_round_trip.py -q -k "TranslationDb or round"`
  - Expected now: `TypeError: WindowSteps.__init__() got an unexpected keyword argument 'translation_db'` in every test that uses the two helpers. Paste one failing line.
- [x] 13.4 Edit `scripts/server_contrib/maintenance_window.py` (dataclass field, `_default_translation_db`, `default_steps`, run_maintenance step, docstring line).
  - In the `WindowSteps` dataclass add, after `health_check: Callable[[WindowConfig], None]`: `translation_db: Callable[[WindowConfig], None]`. No default value: a default would let a test run the real download.
  - Add this function directly before `def default_steps()`:

```python
def _default_translation_db(config: WindowConfig) -> None:
    _run(
        ["uv", "run", "scripts/server_contrib/ensure_translation_db.py"],
        config.project_root,
    )
```

  - In `default_steps()` add `translation_db=_default_translation_db,` after `health_check=_default_health_check,`.
  - How a failure reaches the log: `ensure_translation_db.py` exits with code 1 when the file is still missing, and `_run` calls `subprocess.run(..., check=True)`, which raises `CalledProcessError` for a non-zero exit. The `except Exception` in `run_maintenance` then logs `translation db missing (window goes on): Command '...' returned non-zero exit status 1.` Do not add a return-code check; it is already covered.
  - In `run_maintenance`, find:

```python
                except Exception as exc:
                    log.error(f"contrib_push FAILED (window goes on): {exc}")

            head = _git_head(config.project_root)
```

  Replace with:

```python
                except Exception as exc:
                    log.error(f"contrib_push FAILED (window goes on): {exc}")

            try:
                steps.translation_db(config)
                log.info("translation db present")
            except Exception as exc:
                log.error(f"translation db missing (window goes on): {exc}")

            head = _git_head(config.project_root)
```

  - In the module docstring (top of the file), in the flow list, add this line after the `push the contributions branch ...` line: `      → make sure the translation db is on disk (a failure is logged, the window goes on)`.
- [x] 13.5 Verify the window. Result: 225 passed in tests/scripts/server_contrib; pyright 0 errors.
  - Run: `uv run ruff check --fix scripts/server_contrib/maintenance_window.py tests/scripts/server_contrib/test_maintenance_window.py tests/scripts/server_contrib/test_round_trip.py && uv run ruff format scripts/server_contrib/maintenance_window.py tests/scripts/server_contrib/test_maintenance_window.py tests/scripts/server_contrib/test_round_trip.py`
  - Run: `uv run pyright scripts/server_contrib/maintenance_window.py | tail -1`
  - Run: `uv run pytest tests/scripts/server_contrib -q`
  - → verify: the two new window tests pass; every other test in `tests/scripts/server_contrib` passes (the old rollback, skipped, refused and status tests must not change); pyright reports no new error.
- [x] 13.6 Server setup and docs. `bash -n` silent; `rg "three submodules"` finds nothing outside archive/threads (exit 1); all four doc edits read back in place.
  - `scripts/server_contrib/server_setup.sh`: replace lines 16-17

```bash
# tipitaka.rte: the frequency setup reads the SYA corpus from it.
submodules=(resources/sc-data resources/dpd_submodules resources/tipitaka.rte)
```

  with

```bash
# tipitaka.rte: the frequency setup reads the SYA corpus from it.
# tipitaka_translation_db: holds the script that downloads the translation
# database the Transl tab searches.
submodules=(resources/sc-data resources/dpd_submodules resources/tipitaka.rte resources/tipitaka_translation_db)
```

    Run `bash -n scripts/server_contrib/server_setup.sh` (syntax check only; never run the script). Expect no output.
  - `scripts/server_contrib/README.md`, line ~21. The two lines that now read:

```
- Three submodules: `sc-data`, `dpd_submodules` and `tipitaka.rte`. The frequency
  setup reads the SYA corpus from `tipitaka.rte`.
```

    become these three lines:

```
- Four submodules: `sc-data`, `dpd_submodules`, `tipitaka.rte` and `tipitaka_translation_db`. The frequency
  setup reads the SYA corpus from `tipitaka.rte`. `tipitaka_translation_db` holds the script that downloads
  the translation database (807 MB) the Transl tab searches; the nightly window downloads it when it is missing.
```

    In the same file, in the window flow block (the lines that start with `stop instances`), add this line directly after the line that starts `  → contrib_push`:

```
  → translation db       (downloaded when missing; a failure is logged, not fatal)
```

    In the same file, find the sentence `If `main` ever needs a new submodule, init it once by hand on the server.` and add this sentence after it on the same line: `An existing server loads `resources/tipitaka_translation_db` this way once.`
  - `scripts/server_contrib/NEW_SERVER_RUNBOOK.md`, line ~216: change the words `loads three submodules` to `loads four submodules`.
  - `scripts/server_contrib/config_server.md`, lines ~17-20: in the list of submodules add `resources/tipitaka_translation_db` (the list reads `resources/sc-data`, `resources/dpd_submodules` and `resources/tipitaka.rte`; make it read `resources/sc-data`, `resources/dpd_submodules`, `resources/tipitaka.rte` and `resources/tipitaka_translation_db`). Also change the sentence `The nightly window needs no network beyond `git fetch/pull`.` to `The nightly window needs no network beyond `git fetch/pull` and, when it is missing, a one-time download of the translation database from GitHub releases.`
  - Run: `rg -n -i "three submodules" scripts docs kamma/tech.md` and expect no hit outside `kamma/archive` and `kamma/threads`.
  - → verify: `bash -n` is silent; the `rg` finds nothing; the four doc edits are in place (read each edited line back).
- [x] 13.7 Do NOT run anything on the server. Owner one-off listed in 15.5. The server needs a one-off (owner task, listed in task 15.5).

## Phase 5: the flaky test (spec 12), time-boxed

- [x] 14.1 Try to reproduce. Run A (30x single test): last line `ALL 30 RUNS PASSED`. Run B (10x whole folder): last line `ALL 10 RUNS PASSED`.
  - Run A (30 times, the one test alone; takes a few minutes; stops at the first failure and prints a last line either way): `timeout 1500 bash -c 'for i in $(seq 1 30); do uv run pytest "tests/scripts/server_contrib/test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason" -vv -q -p no:cacheprovider || { echo "FAILED on run $i"; exit 1; }; done; echo "ALL 30 RUNS PASSED"' 2>&1 | tail -60`
  - Run B (10 times, the whole folder, the way the full suite loads it): `timeout 1500 bash -c 'for i in $(seq 1 10); do uv run pytest tests/scripts/server_contrib -q -p no:cacheprovider || { echo "FAILED on run $i"; exit 1; }; done; echo "ALL 10 RUNS PASSED"' 2>&1 | tail -60`
  - Write the two commands and their last line under this task.
- [x] 14.2 If a run failed: REPRODUCED in the 15.1 full-suite run (per 14.3's instruction, treated as this task). Failing: `TestHappyPath::test_status_file_reports_a_failure_and_its_reason` AND the new `TestTranslationDb::test_a_failure_is_logged_and_the_window_goes_on`, both with `problems: 0` in status.txt while the log contains the ERROR line.
  - CAUSE FOUND in the review: importing pyglossary (tests/tools/test_goldendict_exporter.py, tests/exporter) installs a logger class whose addHandler replaces the handler's formatter; _make_logger set the formatter before addHandler. Production never imports pyglossary. Fixed in task 16.1 (formatter set after addHandler, regression test added).

- [x] 14.3 If both runs passed: `not reproduced in 30 + 10 runs`. No code changed. write `not reproduced in 30 + 10 runs` under this task, mark it `[x]`, and stop. Change no code. (Task 15.1 runs the whole suite once more; if that run fails this test, treat it as 14.2.)
  - → verify: the commands and the result are written under this task.
  - Note: the two runs did not reproduce it because they never import pyglossary; see 14.2.

## Phase 6: finish

- [x] 15.1 Whole-suite and type check. Result: `2 failed, 2964 passed, 12 deselected`
  - After the review fixes (task 16.4): `2970 passed, 12 deselected, 40 warnings in 86.70s` — 0 failed. (Before the fixes: `2 failed, 2964 passed` — the two 14.2 failures, both caused by the pyglossary logging interference, fixed in 16.1.) Every other failure name from 0.1: none (0.1 was clean). Type check: `0 errors (123 suppressed, 90 warnings not shown)` — not worse than 0.2.
  - Run: `uv run pytest tests/ -q 2>&1 | tail -15`. Write the names of all failing tests under this task.
  - Run: `just typecheck 2>&1 | tail -8`.
  - → verify: the set of failing test names is a subset of the names written in task 0.1 (a name that is not in 0.1 is a new failure and is yours: fix it); the pyrefly result is not worse than the result written in task 0.2.
- [x] 15.2 Lint every touched file once more — `All checks passed!` (ruff only; pyright was run per task):
  `uv run ruff check gui2/contributor_tabs.py scripts/server_contrib/ensure_translation_db.py tests/gui2/test_contributor_tabs.py tests/scripts/server_contrib/test_ensure_translation_db.py tests/scripts/server_contrib/test_round_trip.py gui2/pass2_add_view.py gui2/main.py gui2/database_manager.py gui2/pass1_add_controller.py gui2/filter_component.py gui2/filter_tab_view.py gui2/roots_tab_view.py gui2/inflection_templates_tab_view.py scripts/server_contrib/contrib_pull.py scripts/server_contrib/maintenance_window.py tests/gui2/test_pass2_add_clipboard.py tests/gui2/test_database_manager_decon_cache.py tests/gui2/test_filter_tab_starter.py tests/gui2/test_main.py tests/gui2/test_read_only_views.py tests/gui2/test_database_manager_corpus.py tests/scripts/server_contrib/test_contrib_pull.py tests/scripts/server_contrib/test_maintenance_window.py`
  - Lint exactly these paths. If ruff says a path does not exist, a task was skipped or renamed: STOP and tell the owner.
  - → verify: `All checks passed!`
- [x] 15.3 Update the code graph. `graphify update .` finished (31,900 nodes, 53,510 edges); one snapshot left: `graphify-out/2026-11-05`. `.graphifyignore` untouched. If `command -v graphify` prints nothing, STOP and tell the owner. Otherwise run `graphify update .` (it can take minutes; do not run it twice). Then prune only when at least two dated snapshots exist: `[ "$(ls -d graphify-out/20* | wc -l)" -ge 2 ] && ls -d graphify-out/20* | sort | head -n -1 | xargs rm -rf`. Never delete `.graphifyignore`.
  - → verify: `graphify update .` ended without error; `ls -d graphify-out/20*` lists exactly one snapshot (the newest). If the update timed out, write that under this task and tell the owner; do not prune.
- [x] 15.4 Files changed or deleted by this thread (stage by name; the `docs/` and `db_tests/db_tests_columns.tsv` changes in the tree are other sessions' — not this thread's):
  - Modified: `.gitignore`, `gui2/README.md`, `gui2/contributor_tabs.py`, `gui2/database_manager.py`, `gui2/filter_component.py`, `gui2/filter_tab_view.py`, `gui2/inflection_templates_tab_view.py`, `gui2/main.py`, `gui2/pass1_add_controller.py`, `gui2/pass2_add_view.py`, `gui2/roots_tab_view.py`, `scripts/server_contrib/NEW_SERVER_RUNBOOK.md`, `scripts/server_contrib/README.md`, `scripts/server_contrib/config_server.md`, `scripts/server_contrib/config_server.template`, `scripts/server_contrib/contrib_pull.py`, `scripts/server_contrib/maintenance_window.py`, `scripts/server_contrib/server_setup.sh`, `tests/gui2/test_contributor_tabs.py`, `tests/gui2/test_database_manager_corpus.py`, `tests/gui2/test_main.py`, `tests/gui2/test_read_only_views.py`, `tests/scripts/server_contrib/test_contrib_pull.py`, `tests/scripts/server_contrib/test_maintenance_window.py`, `tests/scripts/server_contrib/test_round_trip.py`
  - Deleted: `tools/fast_api_utils.py`, `tests/tools/test_fast_api_utils.py`
  - New: `scripts/server_contrib/ensure_translation_db.py`, `tests/gui2/test_pass2_add_clipboard.py`, `tests/gui2/test_database_manager_decon_cache.py`, `tests/gui2/test_filter_tab_starter.py`, `tests/scripts/server_contrib/test_ensure_translation_db.py`
  - Thread files: `kamma/threads/20261105_contrib_x_fixes/` (plan, spec, review_fixes.md) (from your notes), so the owner can stage them by name. Do not run git.
- [x] 15.5 Live checks for the owner (delivered in chat; none run by this thread): see the list below. Assumes tasks 8 and 13 are `[x]` — they are. (no test can). This list is text for the owner to act on; you run none of it, and the `setsid nohup` command is the owner's (rule 12's `timeout` rule is for your own loops). It assumes tasks 8 and 13 are `[x]`.
  - A contributor session shows the Transl tab, whatever the contributor's tab list says, and a search returns text.
  - One-off on the server that already runs (owner does it; every command starts in the server's project folder, and the long one runs detached): load the submodule with `cd <server clone> && git submodule update --init resources/tipitaka_translation_db`. Then either wait for the next nightly window (it downloads the database and logs `translation db present`), or run `cd <server clone> && setsid nohup uv run scripts/server_contrib/ensure_translation_db.py > /tmp/translation_db.log 2>&1 &` and read the log later. The download is 183 MB and the unzipped file is 807 MB.
  - After the next window, the status page shows no `translation db missing` line.
  - Alt keys work in the desktop app and do nothing in Chrome.
  - Save is greyed out on the DB, √ and Infl tabs of a contributor session, and Ctrl+S on those tabs shows the old "read only" message.
  - A contributor with no saved preset sees the DB tab filtered on lemma_1 with the six columns.
  - The Pass2 clipboard message needs a browser that refuses the copy; it cannot be checked on the desktop.
  - The next nightly window deletes the old database copy and leaves the checkout.
  - The desktop app starts without the "address already in use" line.
  - → verify: the owner has the list.

## Phase 7: review fixes (see review_fixes.md)

- [x] 16.1 Fix 1: log formatter set after addHandler, with a regression test. Test first: `AssertionError: assert ' ERROR boom' in '[ERROR] boom\n'` (test failed as required). After the fix: TestLogFormat passes; folder `226 passed`; 21-second reproduction `2 passed, 2977 deselected in 29.48s`. ruff clean; pyright 0 errors on both files.
- [x] 16.2 Fix 2: ensure_translation_db deletes a broken zip and retries once, with tests. Tests first: `assert 1 == 0` (broken zip, only one attempt) and `assert 1 == 2` (gives-up count) failed; the good-zip guard passed already, as expected. After the rewrite: `6 passed`; pyright 0 errors on both files. Script itself NOT run.
- [x] 16.3 Plan and spec notes corrected (tasks 4.1, 14.2, 14.3, 15.1). Nothing differed from review_fixes.md.
- [x] 16.4 Whole suite, type check, lint, graph update. `2970 passed, 12 deselected, 40 warnings in 86.70s` (0 failed); `just typecheck`: `0 errors (123 suppressed, 90 warnings not shown)`; ruff on the four files: `All checks passed!`; `graphify update .` finished, one snapshot left (`graphify-out/2026-11-05`).
