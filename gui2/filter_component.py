import re
from typing import Dict, List

import flet as ft

from db.models import DpdHeadword
from gui2.dpd_fields_classes import DpdDropdown
from gui2.toolkit import ToolKit


class FilterComponent(ft.Column):
    """A modular filter component for DPD database filtering."""

    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        # State management
        self.active_filters: List[Dict[str, str]] = []
        self.display_columns: List[str] = []
        self.result_limit: int = 0
        self.filtered_results: List[DpdHeadword] = []
        self.dpd_headword_columns = [c.name for c in DpdHeadword.__table__.columns]

        # UI Controls
        self.filter_rows: List[ft.Row] = []
        self.column_dropdowns: List[ft.Dropdown] = []
        self.regex_inputs: List[ft.TextField] = []
        self.column_checkboxes: List[ft.Checkbox] = []
        self.limit_input: ft.TextField | None = None
        self.results_table: ft.DataTable | None = None
        # Change tracking
        self.modified_cells: Dict[
            tuple[int, str], str
        ] = {}  # {(row_index, column_name): new_value}

        # Validation rules
        # Dict[str, callable] - validation functions for each column
        self.validation_rules = {
            "id": lambda x: x.isdigit() if x else True,
            # Add more validation rules as needed
        }

        # UI Sections
        self.data_filters_container: ft.Column | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the main UI structure for the filter component."""

        # --- Data Filters Section ---
        data_filters_controls = self._create_data_filters_controls()
        data_filters_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Data Filters", size=16, weight=ft.FontWeight.BOLD),
                    width=150,
                ),
                data_filters_controls,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # --- Display Filters Section ---
        display_filters_controls = self._create_display_filters_controls()
        display_filters_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Display Filters", size=16, weight=ft.FontWeight.BOLD),
                    width=150,
                ),
                display_filters_controls,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # --- Results Limit Section ---
        limit_controls = self._create_limit_controls()
        limit_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Results Limit", size=16, weight=ft.FontWeight.BOLD),
                    width=150,
                ),
                limit_controls,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # --- Action Buttons & Results ---
        buttons_section = self._create_buttons_section()
        results_section = self._create_results_section()

        # Assemble all sections
        self.controls.extend(
            [
                data_filters_section,
                ft.Divider(),
                display_filters_section,
                ft.Divider(),
                limit_section,
                ft.Divider(),
                buttons_section,
                results_section,
            ]
        )

    def _create_data_filters_controls(self) -> ft.Column:
        """Create the controls for the data filters section."""
        # 1. Create and store the initial controls
        initial_dropdown = DpdDropdown(
            name="column_selector_0", options=self.dpd_headword_columns
        )
        initial_regex_input = ft.TextField(width=300, hint_text="Enter regex pattern")

        self.column_dropdowns.append(initial_dropdown)
        self.regex_inputs.append(initial_regex_input)

        # 2. Build the layout from the stored controls
        dropdown_container = ft.Container(content=self.column_dropdowns[0], width=250)

        remove_button = ft.IconButton(
            icon=ft.Icons.REMOVE,
            on_click=self._remove_filter_row,
            disabled=True,  # First row is not removable
            tooltip="Remove this filter",
        )

        initial_filter_row = ft.Row(
            [dropdown_container, self.regex_inputs[0], remove_button]
        )
        self.filter_rows.append(initial_filter_row)

        # 3. Create the main container for this section
        self.data_filters_container = ft.Column(
            [initial_filter_row, ft.Row([self._add_filter_button()])]
        )
        return self.data_filters_container

    def _add_filter_button(self) -> ft.ElevatedButton:
        """Create the 'Add Filter' button."""
        return ft.ElevatedButton("Add Filter", on_click=self._add_filter_row)

    def _create_display_filters_controls(self) -> ft.Column:
        """Create the controls for the display filters section."""
        column_names = [column.name for column in DpdHeadword.__table__.columns]
        self.selected_columns_text = ft.Text("Select columns...")
        self.column_checkboxes = []
        self.options_container = ft.Column(visible=False)

        for col_name in column_names:
            is_selected = col_name in ["id", "lemma_1"]
            checkbox = ft.Checkbox(
                label=col_name,
                value=is_selected,
                on_change=self._on_column_checkbox_change,
            )
            self.column_checkboxes.append(checkbox)
            self.options_container.controls.append(checkbox)

        self.dropdown_button = ft.ElevatedButton(
            "Select Columns", on_click=self._toggle_column_options
        )
        return ft.Column(
            [self.selected_columns_text, self.dropdown_button, self.options_container]
        )

    def _create_limit_controls(self) -> ft.Row:
        """Create the controls for the result limit section."""
        self.limit_input = ft.TextField(
            label="Result Limit",
            hint_text="0 for all results",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0",
        )
        return ft.Row([self.limit_input])

    def _create_buttons_section(self) -> ft.Row:
        """Create the action buttons section."""

        apply_button = ft.ElevatedButton("Apply Filters", on_click=self._apply_filters)

        save_button = ft.ElevatedButton("Save Changes", on_click=self._save_changes)

        return ft.Row([apply_button, save_button])

    def _create_results_section(self) -> ft.Column:
        """Create the results display section."""

        # Create a placeholder column to avoid the AssertionError
        placeholder_column = ft.DataColumn(
            ft.Text("ID"),
        )

        self.results_table = ft.DataTable(
            columns=[placeholder_column],
            rows=[],
            border=ft.border.all(2, ft.Colors.BLACK),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_900,  # Dark blue background for headings
            column_spacing=10,
        )

        scrollable_table_container = ft.Column(
            [ft.Row([self.results_table], scroll=ft.ScrollMode.AUTO)],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        return ft.Column(
            [
                ft.Text("Results", size=20, weight=ft.FontWeight.BOLD),
                scrollable_table_container,
            ],
            expand=True,
        )

    def _add_filter_row(self, e: ft.ControlEvent) -> None:
        """Creates and stores new controls, then adds a new filter row to the UI."""
        # 1. Create and store the new controls
        new_index = len(self.column_dropdowns)
        new_dropdown = DpdDropdown(
            name=f"column_selector_{new_index}", options=self.dpd_headword_columns
        )
        new_regex_input = ft.TextField(width=300, hint_text="Enter regex pattern")

        self.column_dropdowns.append(new_dropdown)
        self.regex_inputs.append(new_regex_input)

        # 2. Build the new row from the stored controls
        dropdown_container = ft.Container(content=new_dropdown, width=250)

        remove_button = ft.IconButton(
            icon=ft.Icons.REMOVE,
            on_click=self._remove_filter_row,
            disabled=False,
            tooltip="Remove this filter",
        )

        new_row = ft.Row([dropdown_container, new_regex_input, remove_button])
        self.filter_rows.append(new_row)

        # 3. Insert the new row into the UI
        if self.data_filters_container:
            # Insert before the 'Add Filter' button row
            self.data_filters_container.controls.insert(-1, new_row)
        self.page.update()

    def _remove_filter_row(self, e: ft.ControlEvent) -> None:
        """Remove the specific filter row associated with the button click."""
        row_to_remove = e.control.parent
        if isinstance(row_to_remove, ft.Row) and row_to_remove in self.filter_rows:
            if len(self.filter_rows) > 1:
                try:
                    idx = self.filter_rows.index(row_to_remove)
                    self.filter_rows.pop(idx)
                    self.column_dropdowns.pop(idx)
                    self.regex_inputs.pop(idx)

                    if self.data_filters_container:
                        self.data_filters_container.controls.remove(row_to_remove)
                    self.page.update()
                except (ValueError, IndexError):
                    self._show_error("Error removing filter row.")

    def _toggle_column_options(self, e: ft.ControlEvent) -> None:
        """Toggle the visibility of column options."""
        self.options_container.visible = not self.options_container.visible
        self.page.update()

    def _on_column_checkbox_change(self, e: ft.ControlEvent) -> None:
        """Handle column checkbox changes and update the display text."""
        selected_options = [
            str(checkbox.label) for checkbox in self.column_checkboxes if checkbox.value
        ]
        self.selected_columns_text.value = (
            ", ".join(selected_options) if selected_options else "Select columns..."
        )
        self.page.update()

    def _apply_filters(self, e: ft.ControlEvent) -> None:
        """Apply all active filters and display results."""
        try:
            # Collect active filters
            active_filters = []
            for i, (column_dropdown, regex_input) in enumerate(
                zip(self.column_dropdowns, self.regex_inputs)
            ):
                if column_dropdown.value and regex_input.value:
                    try:
                        # Validate regex pattern
                        re.compile(regex_input.value)
                        active_filters.append(
                            {
                                "column": column_dropdown.value,
                                "pattern": regex_input.value,
                            }
                        )
                    except re.error as ex:
                        self._show_error(
                            f"Invalid regex pattern in filter {i + 1}: {str(ex)}"
                        )
                        return

            # Get display columns
            display_columns = []
            for checkbox in self.column_checkboxes:
                if checkbox.value:
                    display_columns.append(str(checkbox.label))

            # If no columns selected, show all columns
            if not display_columns:
                display_columns = [
                    column.name for column in DpdHeadword.__table__.columns
                ]

            # Get result limit
            result_limit = 0
            if self.limit_input and self.limit_input.value:
                try:
                    result_limit = int(self.limit_input.value)
                except ValueError:
                    self._show_error("Result limit must be a valid integer")
                    return

            # Build and execute query
            query = self.toolkit.db_manager.db_session.query(DpdHeadword)

            # Apply filters
            for filter_info in active_filters:
                column_name = filter_info["column"]
                pattern = filter_info["pattern"]

                # Get the column attribute from DpdHeadword
                column_attr = getattr(DpdHeadword, column_name, None)
                if column_attr is None:
                    self._show_error(f"Column '{column_name}' not found in DpdHeadword")
                    return

                # Apply regex filter using SQLAlchemy's regexp_match
                query = query.filter(column_attr.regexp_match(pattern))

            # Apply limit if specified
            if result_limit > 0:
                query = query.limit(result_limit)

            # Execute query
            self.filtered_results = query.all()

            # Update results table
            self._update_results_table(display_columns)

            # Show success message
            self._show_message(f"Found {len(self.filtered_results)} results")

        except Exception as ex:
            self._show_error(f"Error applying filters: {str(ex)}")

    def _update_results_table(self, display_columns: List[str]) -> None:
        """Update the results table with filtered data."""
        if not self.results_table:
            return

        # Pre-calculate max widths for each column
        max_widths = {}
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

            # Convert char length to pixel width
            estimated_width = min(600, max(80, max_len * 10 + 50))
            max_widths[col_name] = estimated_width

        # Clear existing data
        self.results_table.columns = []
        self.results_table.rows = []

        # Create columns
        for col_name in display_columns:
            self.results_table.columns.append(ft.DataColumn(ft.Text(col_name)))

        # Create rows
        for row_index, result in enumerate(self.filtered_results):
            row_cells = []
            for col_name in display_columns:
                # Get the value for this column
                value = getattr(result, col_name, "")
                # Convert to string if needed
                if value is None:
                    value_str = ""
                elif isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value)
                else:
                    value_str = str(value)

                def make_on_change_handler(r, c):
                    return lambda e: self._on_cell_change(e, r, c)

                text_field = ft.TextField(
                    value=value_str,
                    on_change=make_on_change_handler(row_index, col_name),
                    dense=True,
                    multiline=False,
                    text_align=ft.TextAlign.LEFT,
                    content_padding=5,
                    border=ft.InputBorder.NONE,
                    expand=True,
                )

                cell_container = ft.Container(
                    content=text_field,
                    width=max_widths[col_name],
                    padding=0,
                )

                row_cells.append(ft.DataCell(cell_container))
            self.results_table.rows.append(ft.DataRow(cells=row_cells))

        # Update the page
        self.page.update()

    def _save_changes(self, e: ft.ControlEvent) -> None:
        """Save any changes back to the database."""
        # Check if there are any changes to save
        if not self.modified_cells:
            self._show_message("No changes to save")
            return

        # Validate data before saving
        is_valid, error_message = self._validate_data()
        if not is_valid:
            self._show_error(error_message)
            return

        try:
            # Group changes by row
            changes_by_row: Dict[int, Dict[str, str]] = {}
            for (row_index, col_name), value in self.modified_cells.items():
                if row_index not in changes_by_row:
                    changes_by_row[row_index] = {}
                changes_by_row[row_index][col_name] = value

            # Apply changes to the database
            for row_index, changes in changes_by_row.items():
                # Get the original record
                record = self.filtered_results[row_index]

                # Update the record with new values
                for col_name, value in changes.items():
                    # Convert value to appropriate type if needed
                    if col_name == "id":
                        setattr(record, col_name, int(value))
                    else:
                        setattr(record, col_name, value)

                # Save the updated record
                success, error = self.toolkit.db_manager.update_word_in_db(record)
                if not success:
                    self._show_error(
                        f"Failed to save changes for row {row_index + 1}: {error}"
                    )
                    # Rollback the session
                    self.toolkit.db_manager.db_session.rollback()
                    return

            # Commit the transaction
            self.toolkit.db_manager.db_session.commit()

            # Clear the modified cells tracking
            self.modified_cells.clear()

            # Refresh the results table
            self._refresh_results_table()

            # Show success message
            self._show_message(f"Successfully saved {len(changes_by_row)} records")

        except Exception as ex:
            # Rollback the session in case of any error
            self.toolkit.db_manager.db_session.rollback()
            self._show_error(f"Error saving changes: {str(ex)}")
            # Log the full traceback for debugging
            import traceback

            print(f"Full traceback: {traceback.format_exc()}")

    def _show_message(self, message: str) -> None:
        """Show a message to the user."""
        # Create a snackbar for user feedback
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
        # Create a snackbar for error feedback
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

        # Get the original value
        original_value = getattr(self.filtered_results[row_index], col_name, "")
        if original_value is None:
            original_value = ""
        elif isinstance(original_value, list):
            original_value = ", ".join(str(v) for v in original_value)
        else:
            original_value = str(original_value)

        # If the value has changed from the original, track it
        if new_value != original_value:
            self.modified_cells[key] = new_value
        # If the value is back to original, remove from tracking
        elif key in self.modified_cells:
            del self.modified_cells[key]

    def _refresh_results_table(self) -> None:
        """Refresh the results table with current display columns."""
        # Re-apply the current filters to get updated data
        # We need to collect the current filter values first
        active_filters = []
        for i, (column_dropdown, regex_input) in enumerate(
            zip(self.column_dropdowns, self.regex_inputs)
        ):
            if column_dropdown.value and regex_input.value:
                active_filters.append(
                    {
                        "column": column_dropdown.value,
                        "pattern": regex_input.value,
                    }
                )

        # Get display columns
        display_columns = []
        for checkbox in self.column_checkboxes:
            if checkbox.value:
                display_columns.append(str(checkbox.label))

        # If no columns selected, show all columns
        if not display_columns:
            display_columns = [column.name for column in DpdHeadword.__table__.columns]

        # Get result limit
        result_limit = 0
        if self.limit_input and self.limit_input.value:
            try:
                result_limit = int(self.limit_input.value)
            except ValueError:
                # If there's an error in the limit value, we'll use 0 (no limit)
                pass

        # Build and execute query
        query = self.toolkit.db_manager.db_session.query(DpdHeadword)

        # Apply filters
        for filter_info in active_filters:
            column_name = filter_info["column"]
            pattern = filter_info["pattern"]

            # Get the column attribute from DpdHeadword
            column_attr = getattr(DpdHeadword, column_name, None)
            if column_attr is not None:
                # Apply regex filter using SQLAlchemy's regexp_match
                query = query.filter(column_attr.regexp_match(pattern))

        # Apply limit if specified
        if result_limit > 0:
            query = query.limit(result_limit)

        # Execute query
        self.filtered_results = query.all()

        # Update results table
        self._update_results_table(display_columns)

    def _validate_data(self) -> tuple[bool, str]:
        """Validate the modified data before saving.

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        for (row_index, col_name), value in self.modified_cells.items():
            # Check if there's a specific validation rule for this column
            if col_name in self.validation_rules:
                validator = self.validation_rules[col_name]
                if not validator(value):
                    return (
                        False,
                        f"Invalid value '{value}' for column '{col_name}' in row {row_index + 1}",
                    )

            # Special validation for ID column
            if col_name == "id":
                if not value.isdigit():
                    return False, f"ID must be a valid integer in row {row_index + 1}"

        return True, ""
