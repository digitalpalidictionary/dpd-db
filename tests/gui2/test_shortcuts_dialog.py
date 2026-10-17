"""The Alt+? popup lays out every shortcut it is given, under its group."""

import flet as ft

from gui2.shortcuts_dialog import build_shortcuts_dialog
from gui2.ui_utils import _CANCEL_LABELS


def _texts(dialog: ft.AlertDialog) -> list[str]:
    """Every text in the popup body, in reading order."""
    assert isinstance(dialog.content, ft.Column)
    texts: list[str] = []
    for control in dialog.content.controls:
        if isinstance(control, ft.Text):
            texts.append(control.value)
        elif isinstance(control, ft.Row):
            texts.extend(c.value for c in control.controls if isinstance(c, ft.Text))
    return texts


def test_groups_and_rows_appear_in_order() -> None:
    dialog = build_shortcuts_dialog(
        [("App", [("Ctrl+Q", "Quit")]), ("Tabs", [("Alt+G", "Go to Global")])],
        lambda _: None,
    )

    assert _texts(dialog) == ["App", "Ctrl+Q", "Quit", "Tabs", "Alt+G", "Go to Global"]


def test_no_divider_after_the_last_group() -> None:
    dialog = build_shortcuts_dialog([("App", [("Ctrl+Q", "Quit")])], lambda _: None)

    assert isinstance(dialog.content, ft.Column)
    assert not isinstance(dialog.content.controls[-1], ft.Divider)


def test_escape_can_close_it() -> None:
    def on_close(_: object) -> None:
        pass

    dialog = build_shortcuts_dialog([], on_close)

    # Escape presses a modal popup's Cancel/Close button (cancel_top_dialog).
    assert dialog.modal is True
    button = dialog.actions[0]
    assert isinstance(button, ft.TextButton)
    assert button.content in _CANCEL_LABELS
    assert button.on_click is on_close
