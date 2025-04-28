import flet as ft
from typing import cast
from rich import print


class AppBarUpdater:
    def __init__(self, page: ft.Page) -> None:
        self.page: ft.Page = page

    def update(self, message: str) -> None:
        """Updates the first action item's value in the page's appbar."""
        if not self.page.appbar:
            print("[yellow]Warning:[/yellow] Page appbar is not set.")
            return

        # Type check for standard AppBar
        if isinstance(self.page.appbar, ft.AppBar):
            if not self.page.appbar.actions:
                print("[yellow]Warning:[/yellow] AppBar actions list is empty.")
                return

            action_item = self.page.appbar.actions[0]
            try:
                # Try to cast to TextField which has a value attribute
                text_field = cast(ft.TextField, action_item)
                text_field.value = message
                self.page.update()
            except (AttributeError, TypeError):
                print(
                    f"[yellow]Warning:[/yellow] AppBar action item {type(action_item)} does not support value assignment."
                )
        else:
            print(
                f"[yellow]Warning:[/yellow] Unsupported appbar type: {type(self.page.appbar)}"
            )
