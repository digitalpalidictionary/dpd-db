import re
from typing import TYPE_CHECKING

import flet as ft

from db.models import DpdHeadword
from gui2.toolkit import ToolKit
from gui2.ui_utils import show_global_snackbar

if TYPE_CHECKING:
    from db.models import DpdHeadword


class DpdDatatable(ft.DataTable):
    def __init__(self, columns, rows):
        super().__init__(
            columns=columns,
            rows=rows,
            data_text_style=ft.TextStyle(size=12, color=ft.Colors.GREY_300),
            border=ft.border.all(2, ft.Colors.BLACK),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_900,
            column_spacing=20,
            horizontal_margin=10,
            heading_text_style=ft.TextStyle(
                color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12
            ),
            heading_row_height=30,
            data_row_min_height=30,
            data_row_max_height=float("inf"),
            show_checkbox_column=False,
        )


class ColumnText(ft.Text):
    def __init__(self, text, width):
        super().__init__(
            value=text,
            expand=True,
            width=width,
            show_selection_cursor=True,
        )


class CellTextField(ft.TextField):
    def __init__(self, text):
        super().__init__(
            value=text,
            multiline=True,
            border_radius=10,
            border=ft.InputBorder.NONE,
            text_align=ft.TextAlign.LEFT,
            text_style=ft.TextStyle(
                size=12,
                color=ft.Colors.GREY_300,
            ),
        )


class FilterComponent(ft.Column):
    """A modular filter component for DPD database filtering."""

    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
        data_filters: list[tuple[str, str]] | None = None,
        display_filters: list[str] | None = None,
        limit: int | None = None,
    ) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        # State management
        self.filtered_results: list["DpdHeadword"] = []
        self.dpd_headword_columns = [c.name for c in DpdHeadword.__table__.columns]
        self.display_filters = display_filters
        self.data_filters = data_filters
        self.limit = limit
        self._just_saved: bool = False

        # UI Controls
        self.results_table: ft.DataTable | None = None
        # Change tracking
        self.modified_cells: dict[
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

        self.results_table = DpdDatatable(
            columns=[placeholder_column],
            rows=[],
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
                    show_global_snackbar(self.page, error_msg, "error", 5000)
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
                    show_global_snackbar(self.page, error_msg, "error", 5000)
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

        except Exception as ex:
            error_msg = f"Error applying filters: {str(ex)}"
            show_global_snackbar(self.page, error_msg, "error", 5000)

    def _update_results_table(self, display_columns: list[str]) -> None:
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

        # Calculate column widths based on content
        column_widths = {}
        if self.filtered_results:
            # Calculate max length for each column
            max_lengths = {}
            for col_name in display_columns:
                max_len = len(col_name)
                for result in self.filtered_results:
                    value = getattr(result, col_name, "")
                    if value is None:
                        value_str = ""
                    elif isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value)
                    else:
                        value_str = str(value)
                    max_len = max(max_len, len(value_str))
                max_lengths[col_name] = max_len

            # Calculate proportional widths
            total_max_len = sum(max_lengths.values())
            if total_max_len > 0:
                for col_name in display_columns:
                    # Proportionate width
                    width = (max_lengths[col_name] / total_max_len) * 1200
                    # Apply min/max constraints
                    column_widths[col_name] = max(50, min(width, 800))

        # Create columns
        for col_name in display_columns:
            width = column_widths.get(col_name, 150)  # Default width if no results
            self.results_table.columns.append(
                ft.DataColumn(label=ColumnText(col_name, width))
            )

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

                text_field = CellTextField(text=value_str)

                if col_name == "id":
                    text_field.read_only = True
                    text_field.multiline = False
                else:

                    def make_on_change_handler(r, c):
                        return lambda e: self._on_cell_change(e, r, c)

                    text_field.on_change = make_on_change_handler(row_index, col_name)

                cells.append(ft.DataCell(text_field))

            self.results_table.rows.append(
                ft.DataRow(
                    cells=cells,
                )
            )

        self.page.update()

    def _save_changes(self, e: ft.ControlEvent) -> None:
        """Save any changes back to the database."""
        if not self.modified_cells:
            show_global_snackbar(self.page, "No changes to save", "info", 3000)
            return

        is_valid, error_message = self._validate_data()
        if not is_valid:
            show_global_snackbar(self.page, error_message, "error", 5000)
            return

        try:
            changes_by_row: dict[int, dict[str, str]] = {}
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
                    show_global_snackbar(
                        self.page,
                        f"Failed to save changes for row {row_index + 1}: {error}",
                        "error",
                        5000,
                    )
                    self.toolkit.db_manager.db_session.rollback()
                    return

            self.toolkit.db_manager.db_session.commit()
            self.modified_cells.clear()
            self._just_saved = True
            self._refresh_results_table()
            self._just_saved = False
            show_global_snackbar(
                self.page,
                f"Successfully saved {len(changes_by_row)} records",
                "info",
                4000,
            )

        except Exception as ex:
            self.toolkit.db_manager.db_session.rollback()
            show_global_snackbar(
                self.page, f"Error saving changes: {str(ex)}", "error", 5000
            )
            import traceback

            print(f"Full traceback: {traceback.format_exc()}")

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
