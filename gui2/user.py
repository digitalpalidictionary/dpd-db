import flet as ft

from tools.configger import config_read, config_update


class UsernameManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.username: str | None = None
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

    def get_username(self) -> None:
        self.username: str | None = config_read("gui2", "username")
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
