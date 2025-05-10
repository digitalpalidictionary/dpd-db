import flet as ft
from typing import Generator

from db.models import DpdHeadword
from db_tests.db_tests_manager import DbTestManager, InternalTestRow
from gui2.toolkit import ToolKit


class TestsTabController:
    def __init__(
        self,
        ui,  # TestsTabView
        toolkit: ToolKit,
    ):
        from gui2.tests_tab_view import TestsTabView

        self.ui: TestsTabView = ui
        self.toolkit: ToolKit = toolkit
        self.page: ft.Page = toolkit.page

        self.db_test_manager: DbTestManager = toolkit.db_test_manager

        self._stop_requested: bool = False
        self._current_test_generator: Generator[InternalTestRow, None, None] | None = (
            None
        )
        self._current_test_failures_for_table: list[
            dict[str, DpdHeadword | InternalTestRow]
        ] = []

    # --- DataTable Helper Methods ---

    def _test_definitions_generator(self):
        if not self.db_test_manager.integrity_ok:
            return

        for test_def in self.db_test_manager.internal_tests_list:
            yield test_def

    def handle_run_tests_clicked(
        self,
        e: ft.ControlEvent | None = None,
    ):
        self._stop_requested = False
        self.ui.run_tests_button.disabled = True
        self.ui.stop_tests_button.disabled = False

        self.ui.update_datatable_columns(None)  # Reset/clear datatable
        self._current_test_failures_for_table.clear()
        self.page.update()

        self._current_test_generator = self._test_definitions_generator()
        self._run_next_test_from_generator()

    def _run_next_test_from_generator(self):
        self.ui.clear_all_fields()

        if self._stop_requested:
            self._finalize_test_run("Stopped by user.")
            return

        try:
            if self._current_test_generator is None:
                self._finalize_test_run("Test generator not initialized.")
                return
            current_test = next(self._current_test_generator)
            if self.db_test_manager:
                self.ui.test_number_text.value = str(
                    self.db_test_manager.internal_tests_list.index(current_test) + 1
                )

            # Populate view fields with current test definition
            self.ui.populate_with_test_definition(current_test)
            self.ui.test_name_input.value = current_test.test_name

            # Setup DataTable for the current test
            self.ui.update_datatable_columns(current_test)
            self._current_test_failures_for_table.clear()
            self.page.update()  # Update test name and clear/setup table for new test

            self._process_single_test_definition(current_test)

        except StopIteration:
            self._finalize_test_run("All tests completed.")
        except (
            Exception
        ) as ex:  # Catch any other unexpected error during test iteration
            self._finalize_test_run(f"Error during test run: {ex}")
            print(f"Exception in _run_next_test_from_generator: {ex}")  # For debugging

    def _process_single_test_definition(self, test_def: InternalTestRow):
        self.page.update()

        failing_headwords_for_this_test = (
            # This is the blocking call that runs one test against all DB entries
            self.db_test_manager.run_test_on_all_db_entries(
                test_def,
                self.toolkit.db_manager.db,
            )
        )

        if self._stop_requested:
            return

        if failing_headwords_for_this_test:
            for hw in failing_headwords_for_this_test:
                self._current_test_failures_for_table.append(
                    {"headword": hw, "test_definition": test_def}
                )
                self.ui._add_failure_to_view_datatable(hw, test_def)

            self.page.update()

        else:
            self._run_next_test_from_generator()

    def _finalize_test_run(self, message: str):
        self.ui.run_tests_button.disabled = False
        self.ui.stop_tests_button.disabled = True
        self._current_test_generator = None
        self.page.update()

    def handle_stop_tests_clicked(
        self, e: ft.ControlEvent | None = None
    ):  # Allow None for direct calls
        self._stop_requested = True
        self.ui.stop_tests_button.disabled = True
        self.page.update()

    def handle_next_test_clicked(self, e: ft.ControlEvent | None = None) -> None:
        """Handle Next button click - either run next test or stop if requested."""
        if self._stop_requested:
            self._finalize_test_run("Stopped by user")
        elif self._current_test_generator:
            self._run_next_test_from_generator()
        else:
            self._finalize_test_run("No active test sequence")
