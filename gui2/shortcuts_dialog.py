"""The Alt+? popup: every editor shortcut in one table, grouped by purpose."""

from collections.abc import Callable
from typing import Any

import flet as ft

# (keys, what they do)
Shortcut = tuple[str, str]
ShortcutGroup = tuple[str, list[Shortcut]]

_KEYS_WIDTH = 160


def _shortcut_row(keys: str, action: str) -> ft.Row:
    return ft.Row(
        [
            ft.Text(
                keys,
                width=_KEYS_WIDTH,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.LIGHT_BLUE_200,
            ),
            ft.Text(action, expand=True),
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


def build_shortcuts_dialog(
    groups: list[ShortcutGroup], on_close: Callable[[Any], None]
) -> ft.AlertDialog:
    """Build the popup. Its "Close" button is also what Escape presses."""
    controls: list[ft.Control] = []
    for title, shortcuts in groups:
        controls.append(ft.Text(title, size=16, weight=ft.FontWeight.BOLD))
        controls.extend(_shortcut_row(keys, action) for keys, action in shortcuts)
        controls.append(ft.Divider())
    if controls:
        controls.pop()  # no divider under the last group

    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Keyboard shortcuts"),
        content=ft.Column(controls, scroll=ft.ScrollMode.AUTO, width=650, tight=True),
        actions=[ft.TextButton("Close", on_click=on_close)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
