import subprocess

import flet as ft

from gui2.toolkit import ToolKit
from scripts.backup.backup_dpd_headwords_and_roots import (
    backup_dpd_headwords_and_roots,
)
from tools.paths import ProjectPaths


class GlobalTabView(ft.Column):
    """Global application controls."""

    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        self._message: ft.Text = ft.Text(
            "", color=ft.Colors.BLUE_200, selectable=True, expand=True
        )

        self.controls.extend(
            [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Backup & Quit",
                                        on_click=self._click_backup_quit,
                                        width=250,
                                    ),
                                    self._message,
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Open Internal Tests",
                                        on_click=self._handle_open_test_file,
                                        width=250,
                                    ),
                                    self._message,
                                ]
                            ),
                        ]
                    ),
                    padding=10,
                )
            ]
        )

    def _update_message(self, msg: str) -> None:
        self._message.value = msg
        if hasattr(self, "page") and self.page is not None:
            self.page.update()

    def _click_backup_quit(self, e: ft.ControlEvent) -> None:
        """Run DB backup and close the app window."""
        pth = ProjectPaths()
        self._update_message("Running database backup...")
        try:
            backup_dpd_headwords_and_roots(pth)
            self._update_message("Database backup completed successfully.")
            if (
                hasattr(self, "page")
                and self.page is not None
                and hasattr(self.page, "window")
            ):
                self.page.window.close()
        except Exception as ex:
            self._update_message(f"Backup failed: {ex}")

    def _handle_open_test_file(self, e: ft.ControlEvent) -> None:
        """Opens the main db_tests_columns.tsv file in LibreOffice Calc."""
        test_file_path = self.toolkit.project_paths.internal_tests_path

        if test_file_path.exists():
            subprocess.Popen(["libreoffice", "--calc", str(test_file_path)])
