import csv
from typing import Tuple, List, Dict
import flet as ft
from db_tests.db_tests_manager import InternalTestRow
from gui2.class_mixins import PopUpMixin
from tools.paths import ProjectPaths
from gui2.class_database import DatabaseManager


class TestManager(PopUpMixin):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.current_tests: List[InternalTestRow] = []
        self.test_failures: List[Dict] = []

    def load_tests(self, pth: ProjectPaths) -> None:
        """Load tests from CSV file"""
        with open(pth.internal_tests_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            self.current_tests = [InternalTestRow(**row) for row in reader]

    def run_tests(self, values: Dict[str, str]) -> Tuple[bool, List[Dict]]:
        """Run all loaded tests against current values"""
        self.test_failures = []
        all_passed = True

        for test_number, test in enumerate(self.current_tests, start=1):
            test_passed = True
            test_results = {}
            failed_criteria = []

            # Check each search criterion
            for i in range(1, 7):
                col = getattr(test, f"search_column_{i}")
                sign = getattr(test, f"search_sign_{i}")
                string = getattr(test, f"search_string_{i}")

                if not sign:  # Skip empty criteria
                    continue

                value = values.get(col, "")
                if sign == "equals":
                    test_results[f"test{i}"] = value == string
                elif sign == "does not equal":
                    test_results[f"test{i}"] = value != string
                elif sign == "contains":
                    test_results[f"test{i}"] = string in value
                elif sign == "does not contain":
                    test_results[f"test{i}"] = string not in value
                elif sign == "contains word":
                    test_results[f"test{i}"] = f" {string} " in f" {value} "
                elif sign == "does not contain word":
                    test_results[f"test{i}"] = f" {string} " not in f" {value} "
                elif sign == "is empty":
                    test_results[f"test{i}"] = not value
                elif sign == "is not empty":
                    test_results[f"test{i}"] = bool(value)

                # Record failed criteria details
                if not test_results.get(f"test{i}", True):
                    failed_criteria.append(
                        f"{col} {sign} '{string}' (found: '{value}')"
                    )

            # If any test failed, record detailed failure info
            if not all(test_results.values()):
                all_passed = False
                self.test_failures.append(
                    {
                        "test_name": test.test_name,
                        "test_number": test_number,
                        "failed_criteria": failed_criteria,
                        "error_column": test.error_column,
                    }
                )

        return all_passed, self.test_failures

    def show_failures(self, page: ft.Page) -> None:
        """Display test failures one at a time with action buttons"""
        if not self.test_failures:
            return

        self.current_failure_index = 0
        self._create_failure_dialog()
        self.show_popup(page)
        self._show_current_failure()

    def _create_failure_dialog(self) -> None:
        """Create dialog with action buttons"""
        self.failure_content = ft.Column()

        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Test Failure"),
            content=self.failure_content,
            actions=[
                ft.TextButton("Add to Exceptions", on_click=self._handle_add_exception),
                ft.TextButton("Edit", on_click=self._handle_edit),
                ft.TextButton("Next", on_click=self._handle_next_failure),
                ft.TextButton("Close", on_click=self._handle_popup_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _show_current_failure(self) -> None:
        """Update dialog content for current failure"""
        failure = self.test_failures[self.current_failure_index]

        self.failure_content.controls = [
            ft.Text(
                f"Test #{failure['test_number']}: {failure['test_name']}",
                weight=ft.FontWeight.BOLD,
            ),
            ft.Divider(),
            ft.Text("Failed Criteria:", style=ft.TextThemeStyle.LABEL_LARGE),
            ft.Text("\n".join(failure["failed_criteria"])),
            ft.Divider(),
            ft.Text(
                f"Error Column: {failure['error_column']}",
                style=ft.TextThemeStyle.LABEL_MEDIUM,
            ),
        ]
        self._dialog.update()

    def _handle_add_exception(self, e: ft.ControlEvent) -> None:
        """Add current failure to exceptions list"""
        failure = self.test_failures[self.current_failure_index]
        # TODO: Implement actual exception storage
        print(f"Added exception for test {failure['test_number']}")
        self._handle_next_failure(e)

    def _handle_edit(self, e: ft.ControlEvent) -> None:
        """Close dialog and focus error field"""
        failure = self.test_failures[self.current_failure_index]
        self._handle_popup_close(e)
        # TODO: Implement field focus logic
        print(f"Edit field: {failure['error_column']}")

    def _handle_next_failure(self, e: ft.ControlEvent) -> None:
        """Show next failure or close if last"""
        self.current_failure_index += 1
        if self.current_failure_index < len(self.test_failures):
            self._show_current_failure()
        else:
            self._handle_popup_close(e)
