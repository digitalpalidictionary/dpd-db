# -*- coding: utf-8 -*-
import os

import flet as ft

from tools.configger import config_read, config_update
from tools.server_mode import resolve_role

__all__ = ["UsernameManager", "resolve_role", "resolve_username"]


def resolve_username() -> str | None:
    """Resolve the active username: DPD_GUI2_USERNAME env override (per-instance
    on the server) falls back to config.ini. Returns None when neither is set so
    the desktop first-run dialog still triggers (behaviour unchanged when the
    env var is absent)."""
    return os.environ.get("DPD_GUI2_USERNAME") or config_read("gui2", "username")


class UsernameManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.username: str | None = resolve_username()
        self.role: str | None = resolve_role()
        self.username_field = ft.TextField(
            label="Enter your username",
            autofocus=True,
            on_submit=self._save_username_and_close_dialog,
            width=300,
        )
        self.username_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                [
                    ft.Text("Please enter your username."),
                    self.username_field,
                ],
                tight=True,
            ),
            actions=[
                ft.ElevatedButton(
                    "Save", on_click=self._save_username_and_close_dialog
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def is_server_contributor(self) -> bool:
        """A web (server) contributor: Submit/Update buttons are hidden because
        sync is automated, and desktop shell-outs are disabled. False on desktop
        (role unset or the legacy 'contributor' role)."""
        return self.role == "contributor-server"

    def get_username(self) -> None:
        self.username: str | None = resolve_username()
        if not self.username:
            self.page.open(self.username_dialog)
            self.page.update()

    def _save_username_and_close_dialog(self, e: ft.ControlEvent) -> None:
        if self.username_field.value:
            self.username = self.username_field.value.strip()
        if self.username:
            config_update("gui2", "username", self.username)
            self.username_dialog.open = False
            self.page.update()
        else:
            self.username_field.error_text = "Username cannot be empty!"
            self.username_field.update()

    def is_not_primary(self) -> bool:
        return self.username != "1"
