import subprocess

import flet as ft

from gui2.toolkit import ToolKit
from scripts.backup.backup_dpd_headwords_and_roots import (
    backup_dpd_headwords_and_roots,
)
from scripts.build.anki_updater import main as anki_updater_main
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
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Update Anki Database",
                                        on_click=self._click_update_anki,
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

    def _click_update_anki(self, e: ft.ControlEvent) -> None:
        """Close Anki if open, run anki updater, and show completion message."""
        self._update_message("Closing Anki...")

        try:
            # First, forcefully close any running Anki processes
            subprocess.run(["pkill", "-9", "-f", "anki"], capture_output=True)

            # Wait a few seconds to ensure Anki has released its database locks
            import time

            time.sleep(3)

            # Verify Anki is truly closed by checking for any remaining processes
            result = subprocess.run(
                ["pgrep", "-f", "anki"], capture_output=True, text=True
            )
            if result.returncode == 0:
                self._update_message(
                    "Warning: Anki may still be running, but proceeding anyway..."
                )
                time.sleep(2)  # Give it a bit more time

            # Run the anki updater script
            self._update_message("Updating Anki database...")
            anki_updater_main()

            self._update_message(
                "Anki database update completed successfully! Restarting Anki..."
            )

            # Automatically restart Anki
            try:
                subprocess.Popen(["anki"])
                self._update_message("Anki has been restarted successfully!")
            except Exception as restart_ex:
                self._update_message(
                    f"Anki update completed, but failed to restart Anki: {restart_ex}. You can manually restart Anki now."
                )

        except Exception as ex:
            self._update_message(f"Anki update failed: {ex}")
