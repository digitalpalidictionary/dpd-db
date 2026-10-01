import asyncio
from types import SimpleNamespace
from typing import Any

import flet as ft

from gui2.ui_utils import cancel_top_dialog


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
