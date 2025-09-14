import subprocess
from typing import TYPE_CHECKING, Generator

import flet as ft

from db.models import DpdHeadword
from db_tests.db_tests_manager import DbTestManager, InternalTestRow
from gui2.filter_component import FilterComponent

if TYPE_CHECKING:
    from gui2.tests_tab_view import TestsTabView
from gui2.toolkit import ToolKit


class TestsTabController:
    def __init__(self, view: "TestsTabView", toolkit: ToolKit):
        self.view: "TestsTabView" = view
        self.toolkit: ToolKit = toolkit
        self.page: ft.Page = view.page
        self._stop_requested: bool = False
        self._current_test_generator: Generator[InternalTestRow, None, None] | None = (
            None
        )
        self._db_entries: list[DpdHeadword] | None = None
        self._tests_list: list[InternalTestRow] | None = None

    def handle_run_tests_clicked(self, e: ft.ControlEvent) -> None:
        print("DEBUG: handle_run_tests_clicked called")
        # Step 2: Disable run button
        self.view.set_run_tests_button_disabled_state(True)
        # Step 3: Enable stop button
        self.view.set_stop_tests_button_disabled_state(False)
        # Step 4: Initialize stop flag
        self._stop_requested = False

        # Show progress bar
        self.view.progress_bar.visible = True
        self.view.page.update()

        # Step 5: Load DB/tests
        print("DEBUG: Loading DB and tests")
        self.view.update_test_name("loading database...")
        db_entries, tests_list = self.load_db_and_tests()
        if db_entries is None or tests_list is None:
            print("DEBUG: Error loading DB or tests")
            # Show error in view.test_name_input (red)
            self.view.test_name_input.value = "Error loading DB or tests"
            self.view.test_name_input.color = ft.Colors.RED
            self.view.page.update()
            # Re-enable run, disable stop, return
            self.view.set_run_tests_button_disabled_state(False)
            self.view.set_stop_tests_button_disabled_state(True)
            # Hide progress bar
            self.view.progress_bar.visible = False
            self.view.page.update()
            return

        self._db_entries = db_entries
        self._tests_list = tests_list

        # Step 6: Integrity check
        print("DEBUG: Performing integrity check")
        if not self.integrity_check(tests_list):
            print("DEBUG: Integrity check failed")
            # Re-enable run, disable stop, return
            self.view.set_run_tests_button_disabled_state(False)
            self.view.set_stop_tests_button_disabled_state(True)
            # Hide progress bar
            self.view.progress_bar.visible = False
            self.view.page.update()
            return

        # Initialize the generator
        print("DEBUG: Initializing test generator")
        self._current_test_generator = self._test_definitions_generator()
        # Start the first test
        self._run_next_test_from_generator()

    def _test_definitions_generator(self) -> Generator[InternalTestRow, None, None]:
        """Generator that yields test definitions one by one."""
        print(
            f"DEBUG: _test_definitions_generator started with {len(self._tests_list or [])} tests"
        )
        if self._tests_list is None:
            return
        for test in self._tests_list:
            print(f"DEBUG: _test_definitions_generator yielding test: {test.test_name}")
            yield test
        print("DEBUG: _test_definitions_generator finished")

    def _run_next_test_from_generator(self) -> None:
        """Run the next test from the generator."""
        print("DEBUG: _run_next_test_from_generator called")
        # Check if stop was requested
        if self._stop_requested:
            print("DEBUG: Stop requested, finalizing test run")
            self._finalize_test_run("Stopped by user.")
            return

        # Check if generator is initialized
        if self._current_test_generator is None:
            print("DEBUG: Test generator not initialized")
            self._finalize_test_run("Test generator not initialized.")
            return

        try:
            # Get the next test from the generator
            print("DEBUG: Getting next test from generator")
            current_test = next(self._current_test_generator)
            print(f"DEBUG: Got test: {current_test.test_name}")

            self.view.clear_all_fields()

            # Update view with test number and name
            if self._tests_list:
                test_index = self._tests_list.index(current_test) + 1
                self.view.update_test_number_display(str(test_index))
            self.view.update_test_name(current_test.test_name)

            # Clear filter component
            self.view.set_filter_component(None)
            self.view.page.update()

            # Run the test
            print("DEBUG: Running single test")
            if self._db_entries is None:
                print("DEBUG: DB entries not loaded")
                self._finalize_test_run("DB entries not loaded.")
                return
            failures, query = self.run_single_test(current_test, self._db_entries)
            print(f"DEBUG: Test completed with {len(failures)} failures")

            # Handle failures or success
            if failures:
                print("DEBUG: Handling test failures")
                self._handle_test_failures(current_test, failures, query)
            else:
                print("DEBUG: Test passed, auto-advancing to next test")
                # For passing tests, update UI to indicate success and auto-advance
                self.view.test_name_input.value = f"{current_test.test_name} - PASSED"
                self.view.page.update()
                # Auto-advance to the next test
                self._run_next_test_from_generator()

        except StopIteration:
            print("DEBUG: All tests completed")
            self._finalize_test_run("All tests completed.")
        except Exception as ex:
            print(f"DEBUG: Error during test run: {ex}")
            self._finalize_test_run(f"Error during test run: {ex}")

    def _handle_test_failures(
        self, test: InternalTestRow, failures: list[DpdHeadword], query: str
    ) -> None:
        """Handle the display of test failures."""
        print("DEBUG: _handle_test_failures called")
        # Step 7d-i: Populate view fields
        self.view.populate_with_test_definition(test)

        # Step 7d-ii: Populate exceptions dropdown
        failure_ids = [
            str(failure.id) for failure in failures if failure.id not in test.exceptions
        ]
        limited_ids = failure_ids[:10]
        self.view.exceptions_dropdown.options = [
            ft.dropdown.Option(id) for id in limited_ids
        ]
        self.view.exceptions_dropdown.value = None

        # Populate test_add_exception_dropdown with failure IDs not in test.exceptions (max 10)
        self.view.test_add_exception_dropdown.options = [
            ft.dropdown.Option(id) for id in limited_ids
        ]
        self.view.test_add_exception_dropdown.value = None

        # Step 7d-iii: Update results summary
        displayed_count = min(len(failures), test.iterations)
        total_found = len(failures)
        self.view.update_results_summary_display(displayed_count, total_found)

        # Step 7d-iv: Create and set filter component
        # Create data filters using failure IDs
        if failures:
            # Debug: Print the IDs we're working with
            failure_ids = [
                str(f.id) for f in failures[: min(len(failures), test.iterations)]
            ]
            print(f"DEBUG: Creating data filters with failure IDs: {failure_ids}")

            # Create the regex pattern
            if failure_ids:
                regex_pattern = f"^({'|'.join(failure_ids)})$"
            else:
                regex_pattern = "^$"

            print(f"DEBUG: Regex pattern: {regex_pattern}")
            data_filters = [("id", regex_pattern)]
        else:
            data_filters = []
            print("DEBUG: No failures, creating empty data_filters")

        # Create display filters from test.display_1/2/3 (filter out empty strings)
        display_filters = [
            display
            for display in [test.display_1, test.display_2, test.display_3]
            if display
        ]

        # Refresh the database session to ensure we have the latest connection
        self.toolkit.db_manager.new_db_session()

        # Instantiate FilterComponent
        filter_component = FilterComponent(
            page=self.view.page,
            toolkit=self.toolkit,
            data_filters=data_filters,
            display_filters=display_filters,
            limit=test.iterations,
        )

        # Display in view
        self.view.set_filter_component(filter_component)

        # Step 7d-v: Update query field
        self.view.test_db_query_input.value = query
        self.view.page.update()

    def _finalize_test_run(self, message: str) -> None:
        """Finalize the test run and reset the UI."""
        print(f"DEBUG: _finalize_test_run called with message: {message}")
        self.view.set_run_tests_button_disabled_state(False)
        self.view.set_stop_tests_button_disabled_state(True)
        # Hide progress bar
        self.view.progress_bar.visible = False
        self.view.page.update()
        # Reset generator
        self._current_test_generator = None
        self._db_entries = None
        self._tests_list = None

    def load_db_and_tests(
        self,
    ) -> tuple[list[DpdHeadword] | None, list[InternalTestRow] | None]:
        try:
            db_session = self.toolkit.db_manager.db_session
            db_entries = db_session.query(DpdHeadword).all()
            manager = DbTestManager()
            tests_list = manager.load_tests()
            return (db_entries, tests_list)
        except Exception as e:
            print(f"Error loading DB and tests: {e}")
            return (None, None)

    def integrity_check(self, tests_list: list[InternalTestRow]) -> bool:
        manager = DbTestManager()
        manager.internal_tests_list = tests_list
        result_ok, failures = manager.integrity_check()
        if not result_ok:
            if failures:
                first_failure = failures[0]
                self.view.test_name_input.value = first_failure.test_name
                self.view.test_name_input.color = ft.Colors.RED
                self.view.page.update()
            return False
        return True

    def run_single_test(
        self, test: InternalTestRow, db_entries: list[DpdHeadword]
    ) -> tuple[list[DpdHeadword], str]:
        manager = DbTestManager()
        failures = manager.run_test_on_all_db_entries(test, db_entries)
        failure_ids = [str(failure.id) for failure in failures]
        limited_ids = failure_ids[:10]
        query = f"/^({'|'.join(limited_ids)})$/" if limited_ids else "/^$/"
        return (failures, query)

    def handle_stop_tests_clicked(self, e: ft.ControlEvent) -> None:
        """Handle stop tests button click."""
        self._stop_requested = True
        self.view.clear_all_fields()

    def handle_edit_tests_clicked(self, e: ft.ControlEvent) -> None:
        """Handle edit tests button click."""
        tests_path = self.toolkit.db_test_manager.tests_path
        try:
            subprocess.Popen(["libreoffice", str(tests_path)])
        except FileNotFoundError:
            # Fallback to default editor if libreoffice is not found
            subprocess.Popen(["xdg-open", str(tests_path)])

    def handle_next_clicked(self, e: ft.ControlEvent) -> None:
        """Handle next button click."""
        self.view.clear_all_fields()

    def handle_test_update(self, e: ft.ControlEvent) -> None:
        """Handle update test button click."""
        # Read all test fields from view
        test_name = self.view.test_name_input.value or ""
        iterations = (
            int(self.view.iterations_input.value)
            if self.view.iterations_input.value
            else 0
        )

        # Create a new InternalTestRow with the updated values
        # Note: This is a simplified implementation. In a real scenario, you would need to
        # get the current test index and update that specific test in the manager's list.
        # Also, you would need to map all fields correctly.
        updated_test = InternalTestRow(
            test_name=test_name,
            search_column_1="",
            search_sign_1="",
            search_string_1="",
            search_column_2="",
            search_sign_2="",
            search_string_2="",
            search_column_3="",
            search_sign_3="",
            search_string_3="",
            search_column_4="",
            search_sign_4="",
            search_string_4="",
            search_column_5="",
            search_sign_5="",
            search_string_5="",
            search_column_6="",
            search_sign_6="",
            search_string_6="",
            error_column="",
            exceptions=[],
            iterations=iterations,
            display_1="",
            display_2="",
            display_3="",
        )

        # Save via manager.save_tests()
        self.toolkit.db_test_manager.save_tests()

        # Show success message in view
        # This would require adding a method to the view to show messages

    def handle_add_new_test(self, e: ft.ControlEvent) -> None:
        """Handle add new test button click."""
        # Read fields from view
        test_name = self.view.test_name_input.value or ""
        iterations = (
            int(self.view.iterations_input.value)
            if self.view.iterations_input.value
            else 0
        )

        # Create new InternalTestRow
        new_test = InternalTestRow(
            test_name=test_name,
            search_column_1="",
            search_sign_1="",
            search_string_1="",
            search_column_2="",
            search_sign_2="",
            search_string_2="",
            search_column_3="",
            search_sign_3="",
            search_string_3="",
            search_column_4="",
            search_sign_4="",
            search_string_4="",
            search_column_5="",
            search_sign_5="",
            search_string_5="",
            search_column_6="",
            search_sign_6="",
            search_string_6="",
            error_column="",
            exceptions=[],
            iterations=iterations,
            display_1="",
            display_2="",
            display_3="",
        )

        # Insert after current test in manager's list
        # Note: This is a simplified implementation. In a real scenario, you would need to
        # determine the current test index.
        self.toolkit.db_test_manager.internal_tests_list.append(new_test)

        # Save via manager.save_tests()
        self.toolkit.db_test_manager.save_tests()

        # Clear view
        self.view.clear_all_fields()

    def handle_delete_test(self, e: ft.ControlEvent) -> None:
        """Handle delete test button click."""
        # Show confirmation dialog (if possible in Flet)
        # This is a simplified implementation. In a real scenario, you would need to
        # implement a proper confirmation dialog.
        confirmed = True  # Placeholder for confirmation

        if confirmed:
            # Remove current test from manager's list
            # Note: This is a simplified implementation. In a real scenario, you would need to
            # determine the current test index.
            if self.toolkit.db_test_manager.internal_tests_list:
                self.toolkit.db_test_manager.internal_tests_list.pop()

            # Save via manager.save_tests()
            self.toolkit.db_test_manager.save_tests()

            # Clear view
            self.view.clear_all_fields()

    def handle_add_exception_button(self, e: ft.ControlEvent) -> None:
        """Handle add exception button click."""
        # Get selected ID from dropdown
        selected_id = self.view.test_add_exception_dropdown.value
        if selected_id:
            # Add to current test exceptions via manager
            # Note: This implementation assumes we have access to the current test
            # In a full implementation, you would need to track the current test
            # For now, we'll just print to console as a placeholder
            print(f"Adding exception ID: {selected_id}")

            # Save via manager.save_tests()
            # Note: This would require access to the test manager
            # self.toolkit.db_test_manager.save_tests()

            # Remove ID from dropdown
            self.view.test_add_exception_dropdown.options = [
                option
                for option in (self.view.test_add_exception_dropdown.options or [])
                if option.key != selected_id
            ]
            self.view.test_add_exception_dropdown.value = None

            # Update message in view
            # This would require adding a method to the view to show messages
            # self.view.show_message(f"Added exception: {selected_id}")

            self.view.page.update()

    def handle_test_db_query_copy(self, e: ft.ControlEvent) -> None:
        """Handle copy DB query button click."""
        # Copy query text from view.test_db_query_input to clipboard using pyperclip.copy()
        import pyperclip

        query_text = self.view.test_db_query_input.value or ""
        pyperclip.copy(query_text)

        # Show a snackbar confirmation
        self.page.overlay.append(
            ft.SnackBar(content=ft.Text("Query copied to clipboard"))
        )
        self.page.update()

    def handle_next_test_clicked(self, e: ft.ControlEvent) -> None:
        """Handle next test button click."""
        print("DEBUG: handle_next_test_clicked called")
        self.view.clear_all_fields()
        # Run the next test
        self._run_next_test_from_generator()
