import re
from typing import Dict, List

import flet as ft

from db.models import DpdHeadword
from gui2.toolkit import ToolKit


class FilterComponent(ft.Column):
    """A modular filter component for DPD database filtering."""

    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
        data_filters: List[tuple[str, str]] | None = None,
        display_filters: List[str] | None = None,
        limit: int | None = None,
    ) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        # State management
        self.filtered_results: List[DpdHeadword] = []
        self.dpd_headword_columns = [c.name for c in DpdHeadword.__table__.columns]
        self.display_filters = display_filters
        self.data_filters = data_filters
        self.limit = limit

        # UI Controls
        self.results_table: ft.DataTable | None = None
        # Change tracking
        self.modified_cells: Dict[
            tuple[int, str], str
        ] = {}  # {(row_index, column_name): new_value}

        # Validation rules
        self.validation_rules = {
            "id": lambda x: x.isdigit() if x else True,
        }

        self._build_ui()
        self._apply_filters()

    def _build_ui(self) -> None:
        """Build the main UI structure for the filter component."""
        results_section = self._create_results_section()
        save_button = ft.ElevatedButton("Save Changes", on_click=self._save_changes)

        self.controls.extend(
            [
                results_section,
                ft.Row([save_button]),
            ]
        )

    def _create_results_section(self) -> ft.Column:
        """Create the results display section."""

        # Create a placeholder column to avoid the AssertionError
        placeholder_column = ft.DataColumn(label=ft.Text("ID"))

        self.results_table = ft.DataTable(
            data_text_style=ft.TextStyle(
                size=12, color=ft.Colors.GREY_300
            ),  # 12-point slightly darker than white text
            columns=[placeholder_column],
            rows=[],
            border=ft.border.all(2, ft.Colors.BLACK),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_900,  # Dark blue background for headings
            column_spacing=50,  # Increased column spacing for better readability
            horizontal_margin=10,
            heading_text_style=ft.TextStyle(
                color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12
            ),
            heading_row_height=30,
            data_row_min_height=30,
            data_row_max_height=float("inf"),
            show_checkbox_column=False,
        )

        # Wrap in containers for proper scrolling
        table_container = ft.Container(
            content=self.results_table,
            expand=True,
            width=1350,  # Fixed width for horizontal scrolling
        )

        # Horizontal scroll for wide tables
        horizontal_scroll = ft.Row(
            [table_container],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            alignment=ft.MainAxisAlignment.START,
        )

        # Vertical scroll for tall tables
        scrollable_table_container = ft.Column(
            [horizontal_scroll],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        return ft.Column(
            [scrollable_table_container],
            expand=True,
        )

    def _apply_filters(self) -> None:
        """Apply all active filters and display results."""
        try:
            active_filters = []
            if self.data_filters:
                for column, pattern in self.data_filters:
                    active_filters.append({"column": column, "pattern": pattern})
            else:
                print("DEBUG: No data_filters provided")

            for i, filter_info in enumerate(active_filters):
                try:
                    re.compile(filter_info["pattern"])
                except re.error as ex:
                    error_msg = f"Invalid regex pattern in filter {i + 1}: {str(ex)}"
                    self._show_error(error_msg)
                    return

            display_columns = (
                self.display_filters
                if self.display_filters
                else [column.name for column in DpdHeadword.__table__.columns]
            )

            result_limit = self.limit if self.limit is not None else 0

            # Refresh the database session to ensure we have the latest connection
            self.toolkit.db_manager.new_db_session()
            query = self.toolkit.db_manager.db_session.query(DpdHeadword)

            for filter_info in active_filters:
                column_name = filter_info["column"]
                pattern = filter_info["pattern"]

                column_attr = getattr(DpdHeadword, column_name, None)
                if column_attr is None:
                    error_msg = f"Column '{column_name}' not found in DpdHeadword"
                    self._show_error(error_msg)
                    return

                # Special handling for ID filtering - convert regex pattern to list of IDs
                if column_name == "id":
                    # Extract IDs from the regex pattern like ^(1571|3106|4365|...)$

                    # Match pattern like ^(1571|3106|4365|...)$
                    # Fix the regex pattern - we need to match ^(1571|3106|4365|...)$
                    # The pattern has literal parentheses, not escaped ones
                    match = re.match(r"^\^\(([^)]+)\)\$$", pattern)
                    if match:
                        id_strings = match.group(1).split("|")
                        id_list = []
                        for id_str in id_strings:
                            try:
                                id_list.append(int(id_str))
                            except ValueError:
                                pass  # Skip invalid IDs
                        if id_list:
                            query = query.filter(column_attr.in_(id_list))
                        else:
                            # Fallback to regexp_match if no valid IDs found
                            query = query.filter(column_attr.regexp_match(pattern))
                    else:
                        # Fallback to regexp_match if pattern is not in expected format
                        query = query.filter(column_attr.regexp_match(pattern))
                else:
                    query = query.filter(column_attr.regexp_match(pattern))

            if result_limit > 0:
                query = query.limit(result_limit)

            self.filtered_results = query.all()

            self._update_results_table(display_columns)
            self._show_message(f"Found {len(self.filtered_results)} results")
        except Exception as ex:
            error_msg = f"Error applying filters: {str(ex)}"

            self._show_error(error_msg)

    def _update_results_table(self, display_columns: List[str]) -> None:
        """Update the results table with filtered data."""

        if not hasattr(self, "results_table") or not self.results_table:
            return

        # Clear existing data
        self.results_table.columns = []
        self.results_table.rows = []

        # Handle case where no display columns are specified
        if not display_columns:
            # Add a default column to avoid AssertionError
            self.results_table.columns.append(ft.DataColumn(label=ft.Text("ID")))
            self.page.update()
            return

        # Calculate column widths based on content - adjusted for DataTable's content-based sizing
        # This calculation is currently unused as Flet's DataColumn doesn't support width parameter
        # Keeping this code for potential future use or for influencing other aspects of the UI
        column_widths = {}
        for col_name in display_columns:
            max_len = len(col_name)  # Start with header length
            for result in self.filtered_results:
                value = getattr(result, col_name, "")
                if value is None:
                    value_str = ""
                elif isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value)
                else:
                    value_str = str(value)
                max_len = max(max_len, len(value_str))

            # Adjusted width calculation for more compact to wider columns
            min_width = 10  # Even more compact minimum width
            calculated_width = (
                max_len * 12 + 25
            )  # Slightly more aggressive width calculation
            column_widths[col_name] = max(
                min_width, min(calculated_width, 1350)
            )  # Wider maximum cap

        # Create columns
        for col_name in display_columns:
            self.results_table.columns.append(ft.DataColumn(label=ft.Text(col_name)))

        # Create rows with editable cells
        for row_index, result in enumerate(self.filtered_results):
            cells = []

            for col_name in display_columns:
                value = getattr(result, col_name, "")
                if value is None:
                    value_str = ""
                elif isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value)
                else:
                    value_str = str(value)

                calculated_width = column_widths.get(col_name, 400)

                if col_name == "id":
                    # ID column: read-only, selectable for copying
                    text_field = ft.TextField(
                        value=value_str,
                        read_only=True,
                        dense=True,
                        multiline=False,
                        text_align=ft.TextAlign.LEFT,
                        content_padding=5,
                        border=ft.InputBorder.NONE,
                        width=calculated_width,
                        text_style=ft.TextStyle(size=12, color=ft.Colors.GREY_300),
                    )
                else:

                    def make_on_change_handler(r, c):
                        return lambda e: self._on_cell_change(e, r, c)

                    # Create editable text field for each cell
                    text_field = ft.TextField(
                        value=value_str,
                        on_change=make_on_change_handler(row_index, col_name),
                        dense=True,
                        multiline=True,
                        text_align=ft.TextAlign.LEFT,
                        content_padding=5,
                        border=ft.InputBorder.NONE,
                        width=calculated_width,
                        text_style=ft.TextStyle(size=12, color=ft.Colors.GREY_300),
                    )

                cells.append(ft.DataCell(text_field))

            # Create a function that captures the row_index by value
            def make_on_select_handler(r):
                return lambda e: self._on_row_select(e, r)

            self.results_table.rows.append(
                ft.DataRow(
                    cells=cells,
                    on_select_changed=make_on_select_handler(row_index),
                )
            )

        self.page.update()

    def _save_changes(self, e: ft.ControlEvent) -> None:
        """Save any changes back to the database."""
        if not self.modified_cells:
            self._show_message("No changes to save")
            return

        is_valid, error_message = self._validate_data()
        if not is_valid:
            self._show_error(error_message)
            return

        try:
            changes_by_row: Dict[int, Dict[str, str]] = {}
            for (row_index, col_name), value in self.modified_cells.items():
                if row_index not in changes_by_row:
                    changes_by_row[row_index] = {}
                changes_by_row[row_index][col_name] = value

            for row_index, changes in changes_by_row.items():
                record = self.filtered_results[row_index]

                for col_name, value in changes.items():
                    if col_name == "id":
                        setattr(record, col_name, int(value))
                    else:
                        setattr(record, col_name, value)

                success, error = self.toolkit.db_manager.update_word_in_db(record)
                if not success:
                    self._show_error(
                        f"Failed to save changes for row {row_index + 1}: {error}"
                    )
                    self.toolkit.db_manager.db_session.rollback()
                    return

            self.toolkit.db_manager.db_session.commit()
            self.modified_cells.clear()
            self._refresh_results_table()
            self._show_message(f"Successfully saved {len(changes_by_row)} records")

        except Exception as ex:
            self.toolkit.db_manager.db_session.rollback()
            self._show_error(f"Error saving changes: {str(ex)}")
            import traceback

            print(f"Full traceback: {traceback.format_exc()}")

    def _show_message(self, message: str) -> None:
        """Show a message to the user."""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            action="OK",
            duration=3000,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def _show_error(self, error: str) -> None:
        """Show an error message to the user."""
        snackbar = ft.SnackBar(
            content=ft.Text(f"Error: {error}"),
            action="OK",
            duration=5000,
            bgcolor=ft.Colors.RED_100,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def _on_cell_change(
        self, e: ft.ControlEvent, row_index: int, col_name: str
    ) -> None:
        """Handle cell value changes and track modifications."""
        new_value = e.control.value
        key = (row_index, col_name)

        original_value = getattr(self.filtered_results[row_index], col_name, "")
        if original_value is None:
            original_value = ""
        elif isinstance(original_value, list):
            original_value = ", ".join(str(v) for v in original_value)
        else:
            original_value = str(original_value)

        if new_value != original_value:
            self.modified_cells[key] = new_value
        elif key in self.modified_cells:
            del self.modified_cells[key]

    def _refresh_results_table(self) -> None:
        """Refresh the results table with current display columns."""
        self._apply_filters()

    def _validate_data(self) -> tuple[bool, str]:
        """Validate the modified data before saving."""
        for (row_index, col_name), value in self.modified_cells.items():
            if col_name in self.validation_rules:
                validator = self.validation_rules[col_name]
                if not validator(value):
                    return (
                        False,
                        f"Invalid value '{value}' for column '{col_name}' in row {row_index + 1}",
                    )

            if col_name == "id":
                if not value.isdigit():
                    return False, f"ID must be a valid integer in row {row_index + 1}"

        return True, ""

    def _on_row_select(self, e: ft.ControlEvent, row_index: int) -> None:
        """Handle row selection event."""
        # If FilterComponent supports row selection, implement logic to copy display_1 value to clipboard when a row is selected
        if e.data == "true":  # Row is selected
            # Get the display_1 value for this row
            if self.display_filters and len(self.display_filters) >= 1:
                display_1_column = self.display_filters[0]
                record = self.filtered_results[row_index]
                display_1_value = getattr(record, display_1_column, "")

                # Copy to clipboard
                import pyperclip

                pyperclip.copy(str(display_1_value))

                # Show a snackbar confirmation
                self.page.overlay.append(
                    ft.SnackBar(
                        content=ft.Text(f"Copied {display_1_column} to clipboard")
                    )
                )
                self.page.update()
