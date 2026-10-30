"""Alt+X clears and Ctrl+S saves the open tab, through its own button handlers."""

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import flet as ft
import pytest

from gui2.bold_search_controller import BoldSearchController
from gui2.bold_search_view import BoldSearchView
from gui2.compound_type_tab_view import CompoundTypeTabView
from gui2.filter_tab_view import FilterTabView
from gui2.global_tab_view import GlobalTabView
from gui2.inflection_templates_tab_view import InflectionTemplatesTabView
from gui2.main import (
    ALREADY_OPEN_MESSAGE,
    App,
    claim_session,
    main,
    release_session,
    tab_selection,
)
from gui2.pass1_add_view import Pass1AddView
from gui2.pass1_auto_view import Pass1AutoView
from gui2.pass2_add_view import Pass2AddView
from gui2.pass2_auto_view import Pass2AutoView
from gui2.roots_tab_view import RootsTabView
from gui2.sandhi_find_replace_view import SandhiFindReplaceView
from gui2.spelling_find_replace_view import SpellingFindReplaceView
from gui2.translations_view import TranslationsView

# Tab index -> (view class, the handler its Clear button's on_click calls).
CLEAR_BUTTON_HANDLERS: dict[int, tuple[type, str]] = {
    1: (TranslationsView, "clear_clicked"),
    2: (Pass1AutoView, "handle_clear_click"),
    3: (Pass1AddView, "clear_all_fields"),
    6: (Pass2AutoView, "handle_clear_click"),
    7: (Pass2AddView, "_click_clear_all"),
    8: (SandhiFindReplaceView, "clear_search"),
    9: (SpellingFindReplaceView, "clear_search"),
    11: (FilterTabView, "_clear_filters_clicked"),
    14: (RootsTabView, "_clear_all"),
    15: (CompoundTypeTabView, "_on_clear"),
    16: (InflectionTemplatesTabView, "_clear_all"),
}


# The labels App.build_ui gives the tab bar, in tab order.
TAB_LABELS: list[str] = [
    "Global",
    "Transl",
    "Pass1Auto",
    "Pass1Add",
    "Pass2Pre",
    "Pass2x",
    "Pass2Auto",
    "Pass2Add",
    "'",
    "Sp",
    "Sandhi",
    "DB",
    "Tests",
    "Bold Search",
    "√",
    "CT",
    "Infl",
]


def _key(key: str, *, ctrl: bool = False, alt: bool = False) -> ft.KeyboardEvent:
    return ft.KeyboardEvent(
        name="keyboard_event",
        control=None,  # pyright: ignore[reportArgumentType]
        key=key,
        shift=False,
        ctrl=ctrl,
        alt=alt,
        meta=False,
    )


def _alt_x() -> ft.KeyboardEvent:
    return _key("X", alt=True)


def _ctrl_s() -> ft.KeyboardEvent:
    return _key("S", ctrl=True)


def _app_on_tab(index: int, view: object, *, dialog_open: bool = False) -> App:
    app = App.__new__(App)
    app.tabs = SimpleNamespace(selected_index=index)  # pyright: ignore[reportAttributeAccessIssue]
    app._views = {index: view}  # pyright: ignore[reportAttributeAccessIssue]
    dialog = ft.AlertDialog(modal=True)
    dialog.open = dialog_open
    app.page = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        _dialogs=SimpleNamespace(controls=[dialog]), show_dialog=MagicMock()
    )
    app._tab_bar = SimpleNamespace(  # pyright: ignore[reportAttributeAccessIssue]
        tabs=[SimpleNamespace(label=ft.Text(label)) for label in TAB_LABELS]
    )
    return app


def test_alt_x_covers_exactly_the_listed_tabs() -> None:
    assert set(App._CLEAR_ACTIONS) == set(CLEAR_BUTTON_HANDLERS) | {13}


@pytest.mark.parametrize("index", sorted(CLEAR_BUTTON_HANDLERS))
def test_alt_x_calls_only_that_tabs_clear_handler(index: int) -> None:
    view_class, handler = CLEAR_BUTTON_HANDLERS[index]
    # spec= makes a call to a method the real view lacks raise, so a renamed
    # handler fails here instead of silently doing nothing.
    view = MagicMock(spec=view_class)
    app = _app_on_tab(index, view)

    asyncio.run(app.on_keyboard(_alt_x()))

    assert view.method_calls == [getattr(call, handler)(None)]


def test_alt_x_on_bold_search_calls_the_controller_clear() -> None:
    view = MagicMock(spec=BoldSearchView)
    view.controller = MagicMock(spec=BoldSearchController)
    app = _app_on_tab(13, view)

    asyncio.run(app.on_keyboard(_alt_x()))

    assert view.controller.method_calls == [call.clear_fields(None)]


@pytest.mark.parametrize("index", [0, 4, 5, 10, 12])
def test_alt_x_does_nothing_on_tabs_without_a_clear_button(index: int) -> None:
    view = MagicMock()
    app = _app_on_tab(index, view)

    asyncio.run(app.on_keyboard(_alt_x()))

    assert view.method_calls == []


def test_alt_x_before_the_tab_is_built_does_not_raise() -> None:
    app = _app_on_tab(7, None)
    app._views = {}  # pyright: ignore[reportAttributeAccessIssue]

    asyncio.run(app.on_keyboard(_alt_x()))


@pytest.mark.parametrize(
    ("index", "view_class", "handler"),
    [
        (11, FilterTabView, "_save_changes_clicked"),
        (8, SandhiFindReplaceView, "commit_clicked"),
        (9, SpellingFindReplaceView, "commit_clicked"),
        (14, RootsTabView, "_save_root"),
        (15, CompoundTypeTabView, "_on_save_changes"),
        (16, InflectionTemplatesTabView, "_save_template"),
    ],
)
def test_ctrl_s_calls_that_tabs_save_handler(
    index: int, view_class: type, handler: str
) -> None:
    view = MagicMock(spec=view_class)
    app = _app_on_tab(index, view)

    asyncio.run(app.on_keyboard(_ctrl_s()))

    assert view.method_calls == [getattr(call, handler)(None)]


@pytest.mark.parametrize(
    ("index", "view_class"), [(3, Pass1AddView), (7, Pass2AddView)]
)
def test_ctrl_s_on_add_tabs_tests_then_adds(index: int, view_class: type) -> None:
    view = MagicMock(spec=view_class)
    app = _app_on_tab(index, view)

    asyncio.run(app.on_keyboard(_ctrl_s()))

    assert view.method_calls == [call.test_and_add_to_db()]
    view.test_and_add_to_db.assert_awaited_once()


def test_ctrl_s_on_global_backs_up_and_quits() -> None:
    view = MagicMock(spec=GlobalTabView)
    app = _app_on_tab(0, view)

    asyncio.run(app.on_keyboard(_ctrl_s()))

    assert view.method_calls == [call._click_backup_quit(None)]
    view._click_backup_quit.assert_awaited_once()


def _add_view(view_class: type, tests_pass: bool | None) -> MagicMock:
    """A view whose Test run passes, fails, or never reaches the tests (None)."""
    view = MagicMock(spec=view_class)
    # Left over from the previous word: a run that skips the tests must not
    # be able to save on the strength of it.
    view.test_manager = SimpleNamespace(passed=True)

    def run_tests(e: object) -> None:
        if tests_pass is not None:
            view.test_manager.passed = tests_pass

    view._click_run_tests.side_effect = run_tests
    view.handle_add_to_db_click = MagicMock()
    view._click_add_to_db = AsyncMock()
    return view


def _was_added(view: MagicMock) -> bool:
    return view.handle_add_to_db_click.called or view._click_add_to_db.await_count > 0


@pytest.mark.parametrize("view_class", [Pass1AddView, Pass2AddView])
@pytest.mark.parametrize(
    ("tests_pass", "added"), [(True, True), (False, False), (None, False)]
)
def test_test_and_add_to_db_adds_only_when_tests_pass(
    view_class: type, tests_pass: bool | None, added: bool
) -> None:
    view = _add_view(view_class, tests_pass)

    asyncio.run(view_class.test_and_add_to_db(view))

    view._click_run_tests.assert_called_once_with(None)
    assert _was_added(view) is added


@pytest.mark.parametrize(
    ("key", "index", "view_class"),
    [
        (_alt_x(), 7, Pass2AddView),
        (_ctrl_s(), 7, Pass2AddView),
        (_ctrl_s(), 14, RootsTabView),
    ],
)
def test_keys_do_nothing_while_a_popup_is_open(
    key: ft.KeyboardEvent, index: int, view_class: type
) -> None:
    view = MagicMock(spec=view_class)
    app = _app_on_tab(index, view, dialog_open=True)

    asyncio.run(app.on_keyboard(key))

    assert view.method_calls == []


@pytest.mark.parametrize("key", ["?", "/"])
def test_alt_question_mark_opens_the_shortcuts_popup(key: str) -> None:
    app = _app_on_tab(0, MagicMock())

    asyncio.run(app.on_keyboard(_key(key, alt=True)))

    show_dialog = app.page.show_dialog
    assert isinstance(show_dialog, MagicMock)
    show_dialog.assert_called_once()
    dialog = show_dialog.call_args.args[0]
    assert isinstance(dialog, ft.AlertDialog)
    assert isinstance(dialog.title, ft.Text)
    assert dialog.title.value == "Keyboard shortcuts"


def test_alt_question_mark_does_nothing_while_a_popup_is_open() -> None:
    app = _app_on_tab(0, MagicMock(), dialog_open=True)

    asyncio.run(app.on_keyboard(_key("?", alt=True)))

    show_dialog = app.page.show_dialog
    assert isinstance(show_dialog, MagicMock)
    show_dialog.assert_not_called()


def test_shortcut_list_names_every_tab_jump_and_clear_tab() -> None:
    app = _app_on_tab(0, MagicMock())
    shortcuts = dict(
        (keys, action)
        for _title, rows in app._shortcut_groups()
        for keys, action in rows
        if keys != "Ctrl+S"
    )

    for key, index in App._TAB_JUMP_KEYS.items():
        assert shortcuts[f"Alt+{key}"] == f"Go to {TAB_LABELS[index]}"
    for index in App._CLEAR_ACTIONS:
        assert TAB_LABELS[index] in shortcuts["Alt+X"]


def _server_app(monkeypatch: pytest.MonkeyPatch, tabs: str) -> App:
    """An App built through build_ui as a contributor-server session."""
    monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
    monkeypatch.setenv("DPD_GUI2_TABS", tabs)
    app = App.__new__(App)
    app._visible, app._read_only = tab_selection()  # pyright: ignore[reportAttributeAccessIssue]
    app._start_index = 2  # pyright: ignore[reportAttributeAccessIssue]
    app._focused_tab_index = 2  # pyright: ignore[reportAttributeAccessIssue]
    app._build_lock = threading.RLock()  # pyright: ignore[reportAttributeAccessIssue]
    app._mounted_tabs = set()  # pyright: ignore[reportAttributeAccessIssue]
    app._views = {}  # pyright: ignore[reportAttributeAccessIssue]
    app._loading_bar = ft.ProgressBar()  # pyright: ignore[reportAttributeAccessIssue]
    app._db_init_started = False  # pyright: ignore[reportAttributeAccessIssue]
    app.toolkit = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    dialog = ft.AlertDialog(modal=True)
    dialog.open = False
    app.page = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    app.page._dialogs = SimpleNamespace(controls=[dialog])
    app._view_builders = {  # pyright: ignore[reportAttributeAccessIssue]
        index: (lambda: SimpleNamespace(_save_changes_clicked=MagicMock()))
        for index in range(len(TAB_LABELS))
    }
    app.build_ui()
    return app


def _tab_bar_labels(app: App) -> list[str]:
    return [tab.label.value for tab in app._tab_bar.tabs]  # pyright: ignore[reportAttributeAccessIssue]


def test_tab_selection_is_every_tab_off_the_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
    monkeypatch.setenv("DPD_GUI2_TABS", "DB")
    monkeypatch.setattr("tools.server_mode.config_read", lambda *_: None)
    visible, read_only = tab_selection()
    assert visible == list(range(len(TAB_LABELS)))
    assert read_only == frozenset()


def test_server_shows_base_and_listed_tabs_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "Bold Search,DB")

    assert _tab_bar_labels(app) == ["Pass1Auto", "Pass1Add", "DB", "Bold Search"]
    assert len(app._tab_bodies.controls) == 4
    assert app.tabs.selected_index == 0
    assert app._current_index() == 2


def test_server_alt_jump_to_a_hidden_tab_does_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "Bold Search,DB")

    asyncio.run(app.on_keyboard(_key("P", alt=True)))

    assert app._current_index() == 2


def test_server_alt_jump_selects_a_listed_tab(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "Bold Search,DB")

    asyncio.run(app.on_keyboard(_key("D", alt=True)))

    assert app._current_index() == 11
    assert app.tabs.selected_index == 2
    assert 11 in app._mounted_tabs


def test_server_marks_read_tabs_read_only_and_ctrl_s_reaches_the_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "Bold Search,DB")

    asyncio.run(app.on_keyboard(_key("D", alt=True)))
    asyncio.run(app.on_keyboard(_ctrl_s()))

    db_view = app._views[11]
    assert db_view.read_only is True  # pyright: ignore[reportAttributeAccessIssue]
    db_view._save_changes_clicked.assert_called_once_with(None)  # pyright: ignore[reportAttributeAccessIssue]
    assert not hasattr(app._views[2], "read_only")


def test_server_alt_arrows_stay_inside_the_visible_tabs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "DB")

    asyncio.run(app.on_keyboard(_key("Arrow Left", alt=True)))
    assert app._current_index() == 2
    for _ in range(5):
        asyncio.run(app.on_keyboard(_key("Arrow Right", alt=True)))
    assert app._current_index() == 11


def test_server_shortcut_list_names_only_visible_tabs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "DB")
    rows = dict(
        (keys, action)
        for _title, group in app._shortcut_groups()
        for keys, action in group
        if keys != "Ctrl+S"
    )

    assert rows["Alt+D"] == "Go to DB"
    assert "Alt+P" not in rows
    assert "Pass2Add" not in rows["Alt+X"]


def test_server_warmup_builds_only_visible_tabs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _server_app(monkeypatch, "Bold Search,DB")
    built: list[int] = []
    app._ensure_tab_built = built.append  # pyright: ignore[reportAttributeAccessIssue]

    app._warmup_in_background()

    assert built == [2, 3, 13, 11]


@pytest.fixture
def free_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gui2.main._session_page", None)


def test_the_newest_page_takes_over_and_the_old_one_is_retired(
    free_session: None,
) -> None:
    first, second = MagicMock(), MagicMock()

    claim_session(first)
    claim_session(second)

    first.controls.clear.assert_called_once()
    assert first.on_keyboard_event is None  # a stale Ctrl+S must not save
    shown = first.add.call_args.args[0]
    assert shown.value == ALREADY_OPEN_MESSAGE
    second.add.assert_not_called()
    release_session(first)  # no longer the holder: must not free the session
    claim_session(MagicMock())
    second.add.assert_called_once()  # the third claim retired the second


def test_reload_works_when_the_old_page_never_reported_a_disconnect(
    free_session: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    built = MagicMock()
    monkeypatch.setattr("gui2.main.App", built)
    monkeypatch.setattr("gui2.main.start_dpd_server", MagicMock())
    first, reloaded = MagicMock(), MagicMock()

    main(first)
    main(reloaded)  # F5: Flet never fired first.on_disconnect

    assert built.call_count == 2
    assert reloaded.add.call_count == 0


def test_a_dead_old_page_does_not_break_the_takeover(free_session: None) -> None:
    dead, fresh = MagicMock(), MagicMock()
    dead.add.side_effect = RuntimeError("connection closed")

    claim_session(dead)
    claim_session(fresh)  # must not raise

    claim_session(MagicMock())
    fresh.add.assert_called_once()  # fresh really became the holder


def test_main_releases_the_session_when_the_page_disconnects(
    free_session: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("gui2.main.App", MagicMock())
    monkeypatch.setattr("gui2.main.start_dpd_server", MagicMock())
    first, second = MagicMock(), MagicMock()

    main(first)
    first.on_disconnect(None)
    main(second)

    assert second.add.call_count == 0  # the real App (mocked) was built, no notice
    assert first.add.call_count == 0  # released first, so nothing to retire
