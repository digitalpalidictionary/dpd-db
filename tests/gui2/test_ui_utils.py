import asyncio
import weakref
from types import SimpleNamespace
from typing import Any

import flet as ft

from gui2.ui_utils import cancel_top_dialog, is_inside, request_focus


def _page(*dialogs: ft.DialogControl) -> Any:
    return SimpleNamespace(_dialogs=SimpleNamespace(controls=list(dialogs)))


def _dialog(
    labels: list[str], pressed: list[str], modal: bool = True, open_: bool = True
) -> ft.AlertDialog:
    dialog = ft.AlertDialog(
        modal=modal,
        actions=[
            ft.TextButton(label, on_click=lambda _, label=label: pressed.append(label))
            for label in labels
        ],
    )
    dialog.open = open_
    return dialog


def test_escape_presses_cancel() -> None:
    pressed: list[str] = []
    page = _page(_dialog(["OK", "Cancel"], pressed))
    assert asyncio.run(cancel_top_dialog(page)) is True
    assert pressed == ["Cancel"]


def test_escape_presses_close() -> None:
    pressed: list[str] = []
    page = _page(_dialog(["Add ticked", "Close"], pressed))
    assert asyncio.run(cancel_top_dialog(page)) is True
    assert pressed == ["Close"]


def test_escape_only_cancels_topmost_open_dialog() -> None:
    lower: list[str] = []
    upper: list[str] = []
    closed: list[str] = []
    page = _page(
        _dialog(["Cancel"], lower),
        _dialog(["Cancel"], upper),
        _dialog(["Cancel"], closed, open_=False),
    )
    asyncio.run(cancel_top_dialog(page))
    assert (lower, upper, closed) == ([], ["Cancel"], [])


def test_escape_ignores_snackbar_on_top() -> None:
    pressed: list[str] = []
    snackbar = ft.SnackBar(ft.Text("saved"))
    snackbar.open = True
    page = _page(_dialog(["Cancel"], pressed), snackbar)
    asyncio.run(cancel_top_dialog(page))
    assert pressed == ["Cancel"]


def test_escape_leaves_non_modal_dialog_to_flutter() -> None:
    lower: list[str] = []
    upper: list[str] = []
    page = _page(_dialog(["Cancel"], lower), _dialog(["Cancel"], upper, modal=False))
    assert asyncio.run(cancel_top_dialog(page)) is False
    assert (lower, upper) == ([], [])


def test_escape_leaves_other_overlay_on_top_to_flutter() -> None:
    pressed: list[str] = []
    sheet = ft.BottomSheet(ft.Text("sheet"))
    sheet.open = True
    page = _page(_dialog(["Cancel"], pressed), sheet)
    assert asyncio.run(cancel_top_dialog(page)) is False
    assert pressed == []


def test_escape_does_nothing_without_cancel_button() -> None:
    lower: list[str] = []
    upper: list[str] = []
    page = _page(_dialog(["Cancel"], lower), _dialog(["Save"], upper))
    assert asyncio.run(cancel_top_dialog(page)) is False
    assert (lower, upper) == ([], [])


def _mount(child: ft.BaseControl, parent: ft.BaseControl) -> None:
    # Flet links a mounted control to its parent this way.
    child._parent = weakref.ref(parent)  # pyright: ignore[reportAttributeAccessIssue]


def test_is_inside_finds_a_nested_control() -> None:
    view = ft.Column()
    composite = ft.Column()
    inner = ft.TextField()
    _mount(composite, view)
    _mount(inner, composite)

    assert is_inside(inner, view)
    assert is_inside(view, view)


def test_is_inside_rejects_a_control_in_another_tree() -> None:
    view = ft.Column()
    other_view = ft.Column()
    inner = ft.TextField()
    _mount(inner, other_view)

    assert not is_inside(inner, view)


def test_unmounted_control_is_inside_nothing() -> None:
    assert not is_inside(ft.TextField(), ft.Column())


class _RunNowPage:
    def run_task(self, handler, *args):
        asyncio.run(handler(*args))


def _focusable(error: Exception | None, focused: list[str]) -> Any:
    async def focus() -> None:
        focused.append("focus")
        if error is not None:
            raise error

    return SimpleNamespace(page=_RunNowPage(), focus=focus)


def test_request_focus_focuses_the_control() -> None:
    focused: list[str] = []
    request_focus(_focusable(None, focused))

    assert focused == ["focus"]


def test_request_focus_swallows_an_invoke_timeout() -> None:
    focused: list[str] = []
    request_focus(_focusable(TimeoutError("Timeout waiting for invokeMethod"), focused))

    assert focused == ["focus"]


def test_request_focus_swallows_a_control_removed_before_focus() -> None:
    focused: list[str] = []
    request_focus(
        _focusable(RuntimeError("Control must be added to the page first"), focused)
    )

    assert focused == ["focus"]
