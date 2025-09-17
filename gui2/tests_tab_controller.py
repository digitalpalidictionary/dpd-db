import subprocess
from typing import TYPE_CHECKING, Generator

import flet as ft

from db.models import DpdHeadword
from db_tests.db_tests_manager import DbTestManager, IntegrityFailure, InternalTestRow
from gui2.filter_component import FilterComponent
from gui2.ui_utils import show_global_snackbar
from tools.db_search_string import db_search_string

if TYPE_CHECKING:
    from gui2.tests_tab_view import TestsTabView
import pyperclip

from gui2.toolkit import ToolKit


class TestsTabController:
    def __init__(self, view: "TestsTabView", toolkit: ToolKit):
        self.view: "TestsTabView" = view
        self.toolkit: ToolKit = toolkit
        self.page: ft.Page = view.page
        self._stop_requested: bool = False
        self._reverse_order: bool = False
        self._current_test_generator: Generator[InternalTestRow, None, None] | None = (
            None
        )
        self._current_test_index: int | None = None
        self._db_entries: list[DpdHeadword] | None = None
        self._tests_list: list[InternalTestRow] | None = None
        self._current_failures: list[DpdHeadword] | None = None
        self._integrity_failures: list | None = None
        self._current_integrity_failure = None

    def handle_toggle_test_direction(self, e: ft.ControlEvent) -> None:
        """Toggle the test direction and update the button icon."""
        self._reverse_order = not self._reverse_order
        if self._reverse_order:
            self.view.test_direction_button.icon = ft.Icons.ARROW_BACK
        else:
            self.view.test_direction_button.icon = ft.Icons.ARROW_FORWARD
        self.view.page.update()

    def handle_run_tests_clicked(self, e: ft.ControlEvent) -> None:
        # Step 1: Clear previous integrity failure highlights
        self.view.reset_field_highlights()

        # Step 2: Disable run button and enable stop button
        self.view.set_run_tests_button_disabled_state(True)
        self.view.set_stop_tests_button_disabled_state(False)
        self.view.set_sort_tests_button_disabled_state(True)
        self._stop_requested = False
        self.view.page.update()

        # Step 3: Load tests first
        self.view.update_test_name("Loading tests...")
        tests_list = self.load_tests()
        if tests_list is None:
            self.view.update_test_name("Error loading tests")
            self.view.set_run_tests_button_disabled_state(False)
            self.view.set_stop_tests_button_disabled_state(True)
            self.view.page.update()
            return

        if self._reverse_order:
            tests_list.reverse()

        self._tests_list = tests_list

        # Step 4: Integrity check before loading the DB
        self.view.update_test_name("running integrity check...")
        integrity_result, failures = self.integrity_check(tests_list)
        if not integrity_result:
            self._integrity_failures = failures
            if failures:
                self._load_failing_test_row_and_populate_ui(failures[0])
            self.view.set_run_tests_button_disabled_state(False)
            self.view.set_stop_tests_button_disabled_state(True)
            self.view.page.update()
            return

        # Step 5: Load DB (only if integrity is OK)
        self.view.update_test_name("loading database...")
        db_entries = self.load_db()
        if db_entries is None:
            self.view.update_test_name("Error loading database")
            self.view.set_run_tests_button_disabled_state(False)
            self.view.set_stop_tests_button_disabled_state(True)
            self.view.page.update()
            return

        self._db_entries = db_entries

        # Step 6: Start running tests
        self._current_test_generator = self._test_definitions_generator()
        self._run_next_test_from_generator()

    def _load_failing_test_row_and_populate_ui(self, failure: IntegrityFailure):
        """Populate the UI with the data of a failing test and highlight the invalid field."""
        if not self._tests_list:
            return

        # The test_row from IntegrityFailure is 1-based for the file, and the file has a header.
        # The self._tests_list is 0-based. So, index is test_row - 2.
        test_index = failure.test_row - 2

        if 0 <= test_index < len(self._tests_list):
            test_definition = self._tests_list[test_index]

            self.view.clear_all_fields()
            self.view.populate_with_test_definition(test_definition)

            # Update UI with failure info
            self.view.update_test_number_display(str(failure.test_row - 1))
            self.view.update_test_name(
                f"Integrity Fail: {failure.test_name} - Invalid value: '{failure.invalid_value}'"
            )

            # Highlight the specific field that failed
            self.view.highlight_invalid_field(failure.invalid_field_name)
            self.view.page.update()

    def _test_definitions_generator(self) -> Generator[InternalTestRow, None, None]:
        """Generator that yields test definitions one by one."""
        if self._tests_list is None:
            return
        for test in self._tests_list:
            yield test

    def _run_next_test_from_generator(self) -> None:
        """Run the next test from the generator."""
        # Check if stop was requested
        if self._stop_requested:
            self._finalize_test_run("Stopped by user.")
            return

        # Check if generator is initialized
        if self._current_test_generator is None:
            self._finalize_test_run("Test generator not initialized.")
            return

        try:
            # Get the next test from the generator
            current_test = next(self._current_test_generator)

            # Update view with test number and name
            if self._tests_list:
                self._current_test_index = self._tests_list.index(current_test)
                test_index = self._current_test_index + 1
                self.view.update_test_number_display(str(test_index))
            self.view.update_test_name(current_test.test_name)

            # Clear filter component
            self.view.set_filter_component(None)
            self.view.page.update()

            # Run the test
            if self._db_entries is None:
                self._finalize_test_run("DB entries not loaded.")
                return
            failures = self.run_single_test(current_test, self._db_entries)

            # Handle failures or success
            if failures:
                self._handle_test_failures(current_test, failures)
            else:
                # Auto-advance to the next test
                self._run_next_test_from_generator()

        except StopIteration:
            self._finalize_test_run("All tests completed.")
        except Exception as ex:
            self._finalize_test_run(f"Error during test run: {ex}")

    def _handle_test_failures(
        self,
        test: InternalTestRow,
        failures: list[DpdHeadword],
    ) -> None:
        """Handle the display of test failures."""
        # Step 7d-i: Populate view fields
        self.view.populate_with_test_definition(test)

        # Step 7d-ii: Populate test_add_exception_dropdown with failure IDs not in test.exceptions (max 10)
        failure_ids = [
            str(failure.id) for failure in failures if failure.id not in test.exceptions
        ]
        limited_ids = failure_ids[: test.iterations]
        self.view.test_add_exception_dropdown.options = [
            ft.dropdown.Option(id) for id in limited_ids
        ]
        self.view.test_add_exception_dropdown.value = None

        # Step 7d-v: Update query field
        self.view.test_db_query_input.value = db_search_string(limited_ids)

        # Step 7d-iii: Update results summary
        displayed_count = min(len(failures), test.iterations)
        total_found = len(failures)
        self.view.update_results_summary_display(displayed_count, total_found)

        # Step 7d-iv: Create and set filter component
        # Create data filters using failure IDs
        if failures:
            failure_ids = [
                str(f.id) for f in failures[: min(len(failures), test.iterations)]
            ]

            # Create the regex pattern
            if failure_ids:
                regex_pattern = f"^({'|'.join(failure_ids)})$"
            else:
                regex_pattern = "^$"

            data_filters = [("id", regex_pattern)]
        else:
            data_filters = []

        # Create display filters from test.display_1/2/3 (filter out empty strings), with 'id' first
        dynamic_displays = [
            display
            for display in [test.display_1, test.display_2, test.display_3]
            if display
        ]
        display_filters = ["id"] + dynamic_displays

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

        # Store current failures for batch exception handling
        self._current_failures = failures

        # Display in view
        self.view.set_filter_component(filter_component)

        self.view.page.update()

    def _finalize_test_run(self, message: str) -> None:
        """Finalize the test run and reset the UI."""
        self.view.set_run_tests_button_disabled_state(False)
        self.view.set_stop_tests_button_disabled_state(True)
        self.view.set_sort_tests_button_disabled_state(False)

        self.view.page.update()
        # Reset generator
        self._current_test_generator = None
        self._db_entries = None
        self._tests_list = None

    def load_tests(self) -> list[InternalTestRow] | None:
        try:
            return list(self.toolkit.db_test_manager.internal_tests_list)
        except Exception as e:
            print(f"Error loading tests: {e}")
            return None

    def load_db(self) -> list[DpdHeadword] | None:
        try:
            db_session = self.toolkit.db_manager.db_session
            db_entries = db_session.query(DpdHeadword).all()
            return db_entries
        except Exception as e:
            print(f"Error loading DB: {e}")
            return None

    def integrity_check(self, tests_list: list[InternalTestRow]) -> tuple[bool, list]:
        manager = DbTestManager()
        manager.internal_tests_list = tests_list
        result_ok, failures = manager.integrity_check()
        if not result_ok:
            if failures:
                first_failure = failures[0]
                self.view.update_test_name(f"{first_failure.test_name}")
            return False, failures
        return True, []

    def run_single_test(
        self, test: InternalTestRow, db_entries: list[DpdHeadword]
    ) -> list[DpdHeadword]:
        manager = DbTestManager()
        failures = manager.run_test_on_all_db_entries(test, db_entries)
        return failures

    def handle_stop_tests_clicked(self, e: ft.ControlEvent) -> None:
        """Handle stop tests button click."""
        self._stop_requested = True
        self.view.set_run_tests_button_disabled_state(False)
        self.view.set_stop_tests_button_disabled_state(True)
        self.view.set_sort_tests_button_disabled_state(False)
        self._current_test_generator = None
        self._db_entries = None
        self._tests_list = None
        self.view.clear_all_fields()
        show_global_snackbar(self.page, "Tests stopped.", "info", 2000)

    def handle_sort_tests_clicked(self, e: ft.ControlEvent) -> None:
        """Handle sort tests button click."""
        try:
            # Disable the sort button during sorting
            self.view.set_sort_tests_button_disabled_state(True)
            self.view.page.update()
            
            # Sort the tests
            self.toolkit.db_test_manager.sort_tests_by_name()
            
            # Show success message
            show_global_snackbar(self.page, "Tests sorted successfully!", "info", 3000)
        except Exception as ex:
            show_global_snackbar(self.page, f"Error sorting tests: {ex}", "error", 5000)
        finally:
            # Re-enable the sort button
            self.view.set_sort_tests_button_disabled_state(False)
            self.view.page.update()

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
        if self._current_test_index is None or self._tests_list is None:
            show_global_snackbar(
                self.page,
                "No current test to update. Run tests first.",
                "error",
                5000,
            )
            return

        current_test = self._tests_list[self._current_test_index]

        # Read all test fields from view
        current_test.test_name = (
            self.view.test_name_input.value or current_test.test_name
        )
        try:
            current_test.iterations = int(
                self.view.iterations_input.value or str(current_test.iterations)
            )
        except ValueError:
            current_test.iterations = 10  # Default fallback

        # Read search criteria 1-6
        for i in range(6):
            elements = self.view.search_criteria_elements[i]
            # For dropdowns, .value is a string or None. Convert None to "".
            search_column_value = elements["search_column"].value
            setattr(
                current_test,
                f"search_column_{i + 1}",
                search_column_value if search_column_value is not None else "",
            )
            setattr(
                current_test,
                f"search_sign_{i + 1}",
                elements["search_sign"].value or "",
            )
            setattr(
                current_test,
                f"search_string_{i + 1}",
                elements["search_string"].value or "",
            )

        # Read other fields (dropdowns)
        # For dropdowns, .value is a string or None. Convert None to "".
        error_column_value = self.view.error_column_input.value
        current_test.error_column = (
            error_column_value
            if error_column_value is not None
            else current_test.error_column
        )
        display_1_value = self.view.display_1_input.value
        current_test.display_1 = (
            display_1_value if display_1_value is not None else current_test.display_1
        )
        display_2_value = self.view.display_2_input.value
        current_test.display_2 = (
            display_2_value if display_2_value is not None else current_test.display_2
        )
        display_3_value = self.view.display_3_input.value
        current_test.display_3 = (
            display_3_value if display_3_value is not None else current_test.display_3
        )

        # Parse exceptions from TextField (comma-separated IDs)
        exceptions_str = (self.view.exceptions_textfield.value or "").strip()
        if exceptions_str:
            try:
                exception_ids = [
                    int(id_str.strip())
                    for id_str in exceptions_str.split(",")
                    if id_str.strip()
                ]
                current_test.exceptions = sorted(exception_ids)
            except ValueError:
                show_global_snackbar(
                    self.page,
                    "Invalid exception IDs; keeping existing.",
                    "warning",
                    5000,
                )
        else:
            current_test.exceptions = []

        current_test.notes = self.view.notes_input.value or ""

        try:
            # Save via manager.save_tests()
            self.toolkit.db_test_manager.save_tests()
            show_global_snackbar(
                self.page,
                "Test updated successfully!",
                "info",
                4000,
            )
        except Exception as save_error:
            show_global_snackbar(
                self.page,
                f"Failed to update test: {str(save_error)}",
                "error",
                5000,
            )

    def handle_add_new_test(self, e: ft.ControlEvent) -> None:
        """Handle add new test button click."""
        manager = self.toolkit.db_test_manager
        if self._current_test_index is not None and self._tests_list is not None:
            # Duplicate current test, insert before current to make it active, populate view for editing
            current_test = self._tests_list[self._current_test_index]
            new_test = InternalTestRow(
                test_name=current_test.test_name + " added",
                search_column_1=current_test.search_column_1,
                search_sign_1=current_test.search_sign_1,
                search_string_1=current_test.search_string_1,
                search_column_2=current_test.search_column_2,
                search_sign_2=current_test.search_sign_2,
                search_string_2=current_test.search_string_2,
                search_column_3=current_test.search_column_3,
                search_sign_3=current_test.search_sign_3,
                search_string_3=current_test.search_string_3,
                search_column_4=current_test.search_column_4,
                search_sign_4=current_test.search_sign_4,
                search_string_4=current_test.search_string_4,
                search_column_5=current_test.search_column_5,
                search_sign_5=current_test.search_sign_5,
                search_string_5=current_test.search_string_5,
                search_column_6=current_test.search_column_6,
                search_sign_6=current_test.search_sign_6,
                search_string_6=current_test.search_string_6,
                error_column=current_test.error_column,
                exceptions=[],
                iterations=current_test.iterations,
                display_1=current_test.display_1,
                display_2=current_test.display_2,
                display_3=current_test.display_3,
                notes=current_test.notes,
            )
            # Insert after current
            insert_index = self._current_test_index + 1
            self._tests_list.insert(insert_index, new_test)
            manager.internal_tests_list = self._tests_list
            # Current index now points to new test
            # Save the new test
            try:
                manager.save_tests()
                show_global_snackbar(
                    self.page,
                    f"New test '{new_test.test_name}' added; edit and update to save changes.",
                    "info",
                    4000,
                )
            except Exception as save_error:
                show_global_snackbar(
                    self.page,
                    f"Failed to save new test: {str(save_error)}",
                    "error",
                    5000,
                )
            # Populate view with new test for editing (no clear)
            self.view.populate_with_test_definition(new_test)
            self.view.update_test_number_display(str(self._current_test_index + 1))
            self.page.update()
        else:
            # Standalone: read from view, append, save, clear
            test_name = self.view.test_name_input.value or ""
            iterations = (
                int(self.view.iterations_input.value)
                if self.view.iterations_input.value
                else 10  # Default to 10 like in update
            )

            # Read search criteria 1-6
            search_criteria = {}
            for i in range(6):
                elements = self.view.search_criteria_elements[i]
                # For dropdowns, .value is a string or None. Convert None to "".
                search_column_value = elements["search_column"].value
                search_criteria[f"search_column_{i + 1}"] = (
                    search_column_value if search_column_value is not None else ""
                )
                search_criteria[f"search_sign_{i + 1}"] = (
                    elements["search_sign"].value or ""
                )
                search_criteria[f"search_string_{i + 1}"] = (
                    elements["search_string"].value or ""
                )

            # Read other fields (dropdowns)
            # For dropdowns, .value is a string or None. Convert None to "".
            error_column_value = self.view.error_column_input.value
            error_column = error_column_value if error_column_value is not None else ""
            display_1_value = self.view.display_1_input.value
            display_1 = display_1_value if display_1_value is not None else ""
            display_2_value = self.view.display_2_input.value
            display_2 = display_2_value if display_2_value is not None else ""
            display_3_value = self.view.display_3_input.value
            display_3 = display_3_value if display_3_value is not None else ""

            # Parse exceptions from TextField (comma-separated IDs)
            exceptions_str = (self.view.exceptions_textfield.value or "").strip()
            exceptions = []
            if exceptions_str:
                try:
                    exceptions = [
                        int(id_str.strip())
                        for id_str in exceptions_str.split(",")
                        if id_str.strip()
                    ]
                    exceptions = sorted(exceptions)
                except ValueError:
                    show_global_snackbar(
                        self.page,
                        "Invalid exception IDs for new test; starting with empty list.",
                        "warning",
                        5000,
                    )

            notes = self.view.notes_input.value or ""

            # Create new InternalTestRow
            new_test = InternalTestRow(
                test_name=test_name,
                **search_criteria,
                error_column=error_column,
                exceptions=exceptions,
                iterations=iterations,
                display_1=display_1,
                display_2=display_2,
                display_3=display_3,
                notes=notes,
            )

            # Append to manager's list
            manager.internal_tests_list.append(new_test)

            # Save via manager.save_tests()
            try:
                manager.save_tests()
                show_global_snackbar(
                    self.page,
                    "New test added successfully!",
                    "info",
                    4000,
                )
            except Exception as save_error:
                show_global_snackbar(
                    self.page,
                    f"Failed to save new test: {str(save_error)}",
                    "error",
                    5000,
                )

            # Clear view
            self.view.clear_all_fields()

    def handle_delete_test(self, e: ft.ControlEvent) -> None:
        """Handle delete test button click."""
        # Check if there's a current test to delete
        if self._current_test_index is None or self._tests_list is None:
            show_global_snackbar(
                self.page,
                "No current test to delete. Run tests first.",
                "error",
                5000,
            )
            return

        # Show confirmation dialog (if possible in Flet)
        # For now, we'll proceed with deletion without confirmation
        # In a real implementation, you would show a proper confirmation dialog

        # Remove current test from manager's list
        current_test = self._tests_list[self._current_test_index]
        self._tests_list.pop(self._current_test_index)
        self.toolkit.db_test_manager.internal_tests_list = self._tests_list

        # Save via manager.save_tests()
        try:
            self.toolkit.db_test_manager.save_tests()
            show_global_snackbar(
                self.page,
                f"Test '{current_test.test_name}' deleted successfully!",
                "info",
                4000,
            )
        except Exception as save_error:
            show_global_snackbar(
                self.page,
                f"Failed to delete test: {str(save_error)}",
                "error",
                5000,
            )
            return

        # Trigger the real next button behavior
        self.handle_next_test_clicked(e)

    def handle_add_exception_button(self, e: ft.ControlEvent) -> None:
        """Handle add exception button click."""
        if self._current_test_index is None or self._tests_list is None:
            show_global_snackbar(
                self.page,
                "No current test. Run tests first.",
                "error",
                5000,
            )
            return

        selected_id = self.view.test_add_exception_dropdown.value
        if selected_id:
            exception_id = int(selected_id)
            current_test = self._tests_list[self._current_test_index]

            if exception_id not in current_test.exceptions:
                current_test.exceptions.append(exception_id)
                current_test.exceptions.sort()
                self.toolkit.db_test_manager.internal_tests_list = self._tests_list
                self.toolkit.db_test_manager.save_tests()
                show_global_snackbar(
                    self.page,
                    f"Added exception {selected_id}",
                    "info",
                    3000,
                )
                # Update the exceptions TextField
                self.view.exceptions_textfield.value = ", ".join(
                    map(str, sorted(current_test.exceptions))
                )
                self.page.update()
            else:
                show_global_snackbar(
                    self.page,
                    f"Exception {selected_id} already exists",
                    "warning",
                    3000,
                )

            # Remove from dropdown
            options = self.view.test_add_exception_dropdown.options or []
            self.view.test_add_exception_dropdown.options = [
                ft.dropdown.Option(
                    opt.key,
                    text_style=ft.TextStyle(size=12),
                )
                for opt in options
                if opt.key != selected_id
            ]
            self.view.test_add_exception_dropdown.value = None
            self.page.update()
        else:
            show_global_snackbar(
                self.page,
                "No exception selected",
                "warning",
                3000,
            )

    def handle_test_db_query_copy(self, e: ft.ControlEvent) -> None:
        """Handle copy DB query button click."""
        # Copy query text from view.test_db_query_input to clipboard using pyperclip.copy()

        if self.view.test_db_query_input.value:
            pyperclip.copy(self.view.test_db_query_input.value)

            # Show a snackbar confirmation
            show_global_snackbar(
                self.page,
                "Query copied to clipboard",
                "info",
                3000,
            )

    def handle_add_all_exceptions_clicked(self, e: ft.ControlEvent) -> None:
        """Handle add all exceptions button click."""
        if (
            self._current_test_index is None
            or self._tests_list is None
            or self._current_failures is None
        ):
            show_global_snackbar(
                self.page,
                "No current test or failures. Run tests first.",
                "error",
                5000,
            )
            return

        current_test = self._tests_list[self._current_test_index]
        # Get new failure IDs from limited displayed failures (failures[:test.iterations] excluding existing exceptions)
        new_ids: list[int] = [
            f.id
            for f in self._current_failures[: current_test.iterations]
            if f.id not in current_test.exceptions
        ]

        if not new_ids:
            show_global_snackbar(
                self.page,
                "No new exceptions to add.",
                "info",
                3000,
            )
            return

        # Create confirmation dialog
        def _on_ok_click(e: ft.ControlEvent) -> None:
            # Add all new IDs to exceptions
            current_test.exceptions.extend(new_ids)
            current_test.exceptions.sort()
            # Save via db_test_manager
            if self._tests_list is not None:
                self.toolkit.db_test_manager.internal_tests_list = self._tests_list
            self.toolkit.db_test_manager.save_tests()
            # Update view's exceptions_textfield
            self.view.exceptions_textfield.value = ", ".join(
                map(str, sorted(current_test.exceptions))
            )
            # Update view's test_add_exception_dropdown: filter out added options
            existing_options = self.view.test_add_exception_dropdown.options or []
            self.view.test_add_exception_dropdown.options = [
                ft.dropdown.Option(opt.key)
                for opt in existing_options
                if opt.key is not None
                and opt.key.isdigit()
                and int(opt.key) not in new_ids
            ]
            self.view.test_add_exception_dropdown.value = None
            # Show success snackbar
            show_global_snackbar(
                self.page,
                f"Added {len(new_ids)} exceptions.",
                "info",
                3000,
            )
            # Refresh FilterComponent by re-calling _handle_test_failures
            # This will exclude new exceptions and update the datatable
            if self._current_failures:
                self._handle_test_failures(current_test, self._current_failures)
            # Close dialog
            self.add_all_alert.open = False
            self.page.update()

        def _on_cancel_click(e: ft.ControlEvent) -> None:
            # Close dialog
            self.add_all_alert.open = False
            self.page.update()

        # Create AlertDialog following pass2_add_view.py pattern
        self.add_all_alert = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=[
                    ft.Text("Add Exceptions", color=ft.Colors.RED_900, size=20),
                    ft.Text(
                        f"Add {len(new_ids)} exceptions to '{current_test.test_name}'?"
                    ),
                ],
                height=100,
                width=400,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            actions=[
                ft.TextButton("OK", on_click=_on_ok_click),
                ft.TextButton("Cancel", on_click=_on_cancel_click),
            ],
        )

        # Open the dialog
        self.page.open(self.add_all_alert)
        self.page.update()

    def handle_next_test_clicked(self, e: ft.ControlEvent) -> None:
        """Handle next test button click."""
        self.view.clear_all_fields()
        # Run the next test
        self._run_next_test_from_generator()

    def handle_rerun_test_clicked(self, e: ft.ControlEvent) -> None:
        """Handle rerun test button click: re-run the current test."""
        if self._current_test_index is None or self._tests_list is None:
            return

        current_test = self._tests_list[self._current_test_index]

        # Show snackbar feedback
        self.view.show_snackbar("Rerunning test...", ft.Colors.BLUE_100)

        # Refresh DB entries for fresh data
        try:
            self._db_entries = self.toolkit.db_manager.db_session.query(
                DpdHeadword
            ).all()
        except Exception as ex:
            self.view.update_test_name(f"Error reloading DB: {ex}")
            self.page.update()
            return

        # Copy-paste logic from _run_next_test_from_generator (lines 100-124)
        self.view.clear_all_fields()

        # Update view with test number and name
        test_index = self._current_test_index + 1
        self.view.update_test_number_display(str(test_index))
        self.view.update_test_name(current_test.test_name)

        # Clear filter component
        self.view.set_filter_component(None)
        self.page.update()

        # Run the test
        if self._db_entries is None:
            self._finalize_test_run("DB entries not loaded.")
            return
        failures = self.run_single_test(current_test, self._db_entries)

        # Handle failures or success
        if failures:
            self._handle_test_failures(current_test, failures)
        else:
            # On pass, show success message and stop (no auto-advance)
            self.view.update_test_name(f"Passed: {current_test.test_name}")
            self.page.update()
