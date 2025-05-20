import subprocess
from pathlib import Path

import flet as ft

from db_tests.db_tests_manager import DbTestManager, IntegrityFailure, TestFailure
from gui2.mixins import PopUpMixin
from gui2.pass1_add_view import Pass1AddView
from gui2.pass2_add_view import Pass2AddView
from gui2.toolkit import ToolKit


class GuiTestManager(PopUpMixin):
    def __init__(self, toolkit: ToolKit):
        super().__init__()

        self.toolkit: ToolKit = toolkit
        self.db_test_manager: DbTestManager = self.toolkit.db_test_manager

        self.ui: Pass2AddView
        self.page: ft.Page

        self.passed: bool
        self.failure_list: list[TestFailure] | list[IntegrityFailure]
        self.current_headword = None

    def run_all_tests(self, ui: Pass1AddView | Pass2AddView, dpd_headword):
        self.db_test_manager.load_tests()
        self.current_headword = dpd_headword  # Store the headword
        passed, failure_list = self.db_test_manager.run_all_tests_on_headword(
            dpd_headword
        )
        self.passed = passed
        self.failure_list = failure_list
        self.ui = ui
        self.page = ui.page

        if passed:
            ui.update_message("All tests passed!")
        else:
            ui.update_message(f"{len(failure_list)} tests failed")

            # Highlight error columns
            for f in failure_list:
                if isinstance(f, TestFailure):
                    field = ui.dpd_fields.get_field(f.error_column)
                    if field and hasattr(field, "error_text"):
                        field.error_text = f.test_name
                elif isinstance(f, IntegrityFailure):
                    field = ui.dpd_fields.get_field(f.invalid_field_name)
                    ui.update_message(
                        f"error in TSV: {f.test_row} {f.test_name} {f.invalid_field_name} {f.invalid_value}"
                    )
                    return

            self.show_failures()

    def show_failures(self) -> None:
        """Display test failures one at a time with action buttons"""

        if not self.failure_list:
            return

        self.current_failure_index = 0
        self._create_failure_dialog()
        self.show_popup(self.page)
        self._show_current_failure()

    def _create_failure_dialog(self) -> None:
        """Create dialog with action buttons"""
        self.failure_content = ft.Column(
            height=120,
            expand=False,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._dialog = ft.AlertDialog(
            modal=True,
            content=self.failure_content,
            actions=[
                ft.TextButton("Edit", on_click=self._handle_edit),
                ft.TextButton("Add to Exceptions", on_click=self._handle_add_exception),
                ft.TextButton("Next", on_click=self._handle_next_failure),
                ft.TextButton("Close", on_click=self._handle_popup_close),
                ft.TextButton("Open Tests TSV", on_click=self._handle_open_test_file),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            actions_padding=20,
            content_padding=20,
        )

    def _show_current_failure(self) -> None:
        """Update dialog content for current failure"""
        failure = self.failure_list[self.current_failure_index]

        self.failure_content.controls = [
            ft.Text(
                "Test Failed",
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                str(failure.test_row),
                color=ft.Colors.BLUE_200,
                selectable=True,
            ),
            ft.Text(
                f"{failure.test_name}",
                selectable=True,
            ),
            # Display relevant info based on failure type
            ft.Text(
                f"Column: {failure.error_column}"
                if isinstance(failure, TestFailure)
                else f"Field: {failure.invalid_field_name}",
                selectable=True,
            ),
            ft.Text(
                f"Value: {failure.invalid_value}"
                if isinstance(failure, IntegrityFailure)
                else "",
                selectable=True,
                visible=isinstance(
                    failure, IntegrityFailure
                ),  # Only show if IntegrityFailure
            ),
        ]
        self._dialog.update()

    def _handle_add_exception(self, e: ft.ControlEvent) -> None:
        """Add current failure's headword ID to exceptions list"""
        if self.current_failure_index >= len(self.failure_list):
            return  # Safety check

        failure = self.failure_list[self.current_failure_index]

        # Ensure we have a headword and it's a TestFailure
        if self.current_headword and isinstance(failure, TestFailure):
            test_row = failure.test_row
            test_name = failure.test_name
            headword_id = int(self.current_headword.id)

            self.ui.update_message(f"adding exception for {test_row}: {test_name}")

            success = self.db_test_manager.add_exception(test_name, headword_id)

            if success:
                self.ui.update_message(f"added exception for {test_name}")
            else:
                self.ui.update_message(f"Failed to add exception for {test_name}")

            # Move to the next failure regardless of success/failure
            self._handle_next_failure(e)

        elif not isinstance(failure, TestFailure):
            self.ui.update_message(
                f"Cannot add exception for IntegrityFailure: {failure.test_name}"
            )
            self._handle_next_failure(e)
        else:
            # If current_headword is not set, still try to move to the next failure
            # or close if it's the last one, mimicking the "Next" button behavior.
            self.ui.update_message(
                "Error: current_headword not set. Attempting to proceed."
            )
            self._handle_next_failure(e)  # Always behave like 'Next'

    def _handle_open_test_file(self, e: ft.ControlEvent) -> None:
        """Opens the main db_tests_columns.tsv file in LibreOffice Calc."""
        test_file_path = Path(
            "/home/bodhirasa/Code/dpd-db/db_tests/db_tests_columns.tsv"
        )

        if test_file_path.exists():
            self.ui.update_message(f"Opening test file: {test_file_path}")
            try:
                subprocess.Popen(["libreoffice", "--calc", str(test_file_path)])
                self._handle_popup_close(e)  # Close popup after attempting to open
            except FileNotFoundError:
                self.ui.update_message("Error: 'libreoffice' command not found.")
            except Exception as sub_err:
                self.ui.update_message(
                    f"Error opening file with LibreOffice: {sub_err}"
                )
        else:
            self.ui.update_message(
                f"Error: Test file not found at expected path: {test_file_path}"
            )

    def _handle_edit(self, e: ft.ControlEvent) -> None:
        """Close dialog and focus error field"""
        failure = self.failure_list[self.current_failure_index]
        self._handle_popup_close(e)
        # TODO: Implement field focus logic
        self.ui.update_message(f"Edit field: {failure.test_name}")

    def _handle_next_failure(self, e: ft.ControlEvent) -> None:
        """Show next failure or close if last"""
        self.current_failure_index += 1
        if self.current_failure_index < len(self.failure_list):
            self._show_current_failure()
        else:
            self._handle_popup_close(e)
