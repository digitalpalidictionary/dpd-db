"""Alt+X clears and Ctrl+S saves the open tab, through its own button handlers."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import flet as ft
import pytest

from gui2.bold_search_controller import BoldSearchController
from gui2.bold_search_view import BoldSearchView
from gui2.compound_type_tab_view import CompoundTypeTabView
from gui2.filter_tab_view import FilterTabView
from gui2.global_tab_view import GlobalTabView
from gui2.main import App
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
