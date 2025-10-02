from typing import List

import flet as ft

from db.models import DpdHeadword
from gui2.dpd_fields_classes import DpdDropdown, DpdTextField
from gui2.filter_component import FilterComponent
from gui2.toolkit import ToolKit

LABEL_COLOUR = ft.Colors.GREY_500

DEFAULT_LIMIT = 50


class FilterTabView(ft.Column):
    """Filter tab for database filtering functionality."""

    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
        data_filters: List[tuple[str, str]] = [("root_key", ""), ("family_root", "")],
        display_filters: List[str] = [
            "id",
            "lemma_1",
            "meaning_1",
            "meaning_lit",
            "root_key",
            "family_root",
        ],
        limit: int = 50,
    ) -> None:
        super().__init__(expand=True, spacing=5, scroll=ft.ScrollMode.AUTO, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        self.dpd_headword_columns = [c.name for c in DpdHeadword.__table__.columns]

        # UI Controls
        self.filter_rows: List[ft.Row] = []
        self.column_dropdowns: List[ft.Dropdown] = []
        self.regex_inputs: List[ft.TextField] = []
        self.column_checkboxes: List[ft.Checkbox] = []
        self.limit_input: ft.TextField | None = None
        self.data_filters_container: ft.Column | None = None
        self.selected_columns_container: ft.Row | None = None
        self.options_container: ft.Container | None = None
        self.dropdown_button: ft.ElevatedButton | None = None
        self.preset_dropdown: ft.Dropdown | None = None
        self.save_preset_button: ft.ElevatedButton | None = None
        self.delete_preset_button: ft.ElevatedButton | None = None

        self.filter_component_container = ft.Container(
            content=ft.Column([], expand=True, scroll=ft.ScrollMode.AUTO),
            expand=True,
        )

        self._build_ui()

        # Load the first preset as default if available, otherwise use provided defaults
        first_preset_data = self.toolkit.filter_presets_manager.get_first_preset()
        if first_preset_data and isinstance(first_preset_data, dict):
            # Load preset data
            preset_data_filters = first_preset_data.get("data_filters", data_filters)
            preset_display_filters = first_preset_data.get(
                "display_filters", display_filters
            )
            preset_limit = first_preset_data.get("limit", limit)

            # Ensure correct types before passing to initialize_filters
            if (
                isinstance(preset_data_filters, list)
                and isinstance(preset_display_filters, list)
                and isinstance(preset_limit, int)
            ):
                self._initialize_filters(
                    preset_data_filters, preset_display_filters, preset_limit
                )
            else:
                # Fallback to provided defaults if types don't match
                self._initialize_filters(data_filters, display_filters, limit)
        else:
            # Use provided defaults
            self._initialize_filters(data_filters, display_filters, limit)

    def _initialize_filters(
        self,
        data_filters: List[tuple[str, str]] | None = None,
        display_filters: List[str] | None = None,
        limit: int | None = None,
    ):
        """Initialize the filter with predefined values."""
        if data_filters and isinstance(data_filters, list):
            # Ensure we have enough filter rows
            while len(self.column_dropdowns) < len(data_filters):
                self._add_filter_row(None)

            # Update existing filter rows
            for i, item in enumerate(data_filters):
                if isinstance(item, (list, tuple)) and len(item) >= 1:
                    column = item[0]
                    value = item[1] if len(item) > 1 else ""
                    if i < len(self.column_dropdowns):
                        self.column_dropdowns[i].value = column
                        self.regex_inputs[i].value = value

        if display_filters and isinstance(display_filters, list):
            for checkbox in self.column_checkboxes:
                if checkbox.label and isinstance(checkbox.label, str):
                    checkbox.value = checkbox.label in display_filters
            self._on_column_checkbox_change(None)

        if limit is not None and isinstance(limit, int) and self.limit_input:
            self.limit_input.value = str(limit)

    def _build_ui(self) -> None:
        """Build the main UI structure for the filter tab view."""

        # --- Data Filters Section ---
        data_filters_controls = self._create_data_filters_controls()
        data_filters_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Data Filters", size=14, color=LABEL_COLOUR),
                    width=150,
                ),
                data_filters_controls,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # --- Display Filters Section ---
        display_filters_controls = self._create_display_filters_controls()
        display_filters_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Display Filters", size=14, color=LABEL_COLOUR),
                    width=150,
                ),
                display_filters_controls,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # --- Results Limit Section ---
        limit_controls = self._create_limit_controls()
        limit_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Results Limit", size=14, color=LABEL_COLOUR),
                    width=150,
                ),
                limit_controls,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # --- Action Buttons & Results ---
        apply_button = ft.ElevatedButton(
            "Apply Filters", on_click=self._apply_filters_clicked
        )
        clear_button = ft.ElevatedButton(
            "Clear Filters", on_click=self._clear_filters_clicked
        )
        reset_button = ft.ElevatedButton(
            "Reset to Default", on_click=self._reset_to_default_clicked
        )
        # --- Preset Controls ---
        preset_controls = self._create_preset_controls()

        buttons_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Filters", size=14, color=LABEL_COLOUR),
                    width=150,
                ),
                apply_button,
                clear_button,
                reset_button,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        preset_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Presets", size=14, color=LABEL_COLOUR),
                    width=150,
                ),
                preset_controls,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        # ft.Row([apply_button, clear_button])

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
                ft.Divider(),
                preset_section,
                ft.Divider(),
                self.filter_component_container,
            ]
        )

    def _create_data_filters_controls(self) -> ft.Column:
        """Create the controls for the data filters section."""
        initial_dropdown = DpdDropdown(
            name="column_selector_0", options=self.dpd_headword_columns
        )
        initial_regex_input = DpdTextField(
            name="regex_pattern_0",
            multiline=False,
            on_submit=self._apply_filters_clicked,
        )
        initial_regex_input.hint_text = "enter regex"
        initial_regex_input.hint_style = ft.TextStyle(color=LABEL_COLOUR, size=10)

        self.column_dropdowns.append(initial_dropdown)
        self.regex_inputs.append(initial_regex_input)

        dropdown_container = ft.Container(content=self.column_dropdowns[0], width=250)

        remove_button = ft.IconButton(
            icon=ft.Icons.REMOVE,
            on_click=self._remove_filter_row,
            disabled=True,
            tooltip="Remove this filter",
        )

        initial_filter_row = ft.Row(
            [dropdown_container, self.regex_inputs[0], remove_button]
        )
        self.filter_rows.append(initial_filter_row)

        self.data_filters_container = ft.Column(
            [initial_filter_row, ft.Row([self._add_filter_button()])]
        )
        return self.data_filters_container

    def _add_filter_button(self) -> ft.ElevatedButton:
        """Create the 'Add Filter' button."""
        return ft.ElevatedButton("Add Filter", on_click=self._add_filter_row)

    def _add_filter_row(self, e: ft.ControlEvent | None) -> None:
        """Creates and stores new controls, then adds a new filter row to the UI."""
        new_index = len(self.column_dropdowns)
        new_dropdown = DpdDropdown(
            name=f"column_selector_{new_index}", options=self.dpd_headword_columns
        )
        new_regex_input = DpdTextField(
            name=f"regex_pattern_{new_index}",
            multiline=False,
            on_submit=self._apply_filters_clicked,
        )
        new_regex_input.hint_text = "enter regex"
        new_regex_input.hint_style = ft.TextStyle(color=LABEL_COLOUR, size=10)

        self.column_dropdowns.append(new_dropdown)
        self.regex_inputs.append(new_regex_input)

        dropdown_container = ft.Container(content=new_dropdown, width=250)

        remove_button = ft.IconButton(
            icon=ft.Icons.REMOVE,
            on_click=self._remove_filter_row,
            disabled=False,
            tooltip="Remove this filter",
        )

        new_row = ft.Row([dropdown_container, new_regex_input, remove_button])
        self.filter_rows.append(new_row)

        if self.data_filters_container:
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
                    pass  # Should not happen

    def _create_display_filters_controls(self) -> ft.Column:
        """Create the controls for the display filters section."""
        column_names = [column.name for column in DpdHeadword.__table__.columns]
        self.selected_columns_container = ft.Row([], wrap=True)
        self.column_checkboxes = []

        # Create checkboxes in a scrollable column that always shows scrollbar
        checkboxes_column = ft.Column(
            scroll=ft.ScrollMode.ALWAYS, height=200, auto_scroll=False
        )

        for col_name in column_names:
            is_selected = col_name in ["id", "lemma_1"]
            checkbox = ft.Checkbox(
                label=col_name,
                value=is_selected,
                on_change=self._on_column_checkbox_change,
            )
            self.column_checkboxes.append(checkbox)
            checkboxes_column.controls.append(checkbox)

        self.options_container = ft.Container(
            content=checkboxes_column, visible=False, expand=False
        )

        self.dropdown_button = ft.ElevatedButton(
            "Select Columns", on_click=self._toggle_column_options
        )
        return ft.Column(
            [
                self.selected_columns_container,
                self.dropdown_button,
                self.options_container,
            ]
        )

    def _toggle_column_options(self, e: ft.ControlEvent) -> None:
        """Toggle the visibility of column options."""
        if self.options_container:
            self.options_container.visible = not self.options_container.visible
        self.page.update()

    def _on_column_checkbox_change(self, e: ft.ControlEvent | None) -> None:
        """Handle column checkbox changes and update the display text."""
        selected_options = [
            str(checkbox.label) for checkbox in self.column_checkboxes if checkbox.value
        ]

        # Clear the container
        if self.selected_columns_container:
            self.selected_columns_container.controls.clear()

            # Add blue rounded buttons for each selected option
            for option in selected_options:
                button = ft.Container(
                    content=ft.Text(option, size=14, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.BLUE_700,
                    border_radius=20,
                    padding=ft.Padding(10, 2, 10, 2),
                )
                self.selected_columns_container.controls.append(button)

            # If no options selected, show a placeholder
            if not selected_options:
                placeholder = ft.Text("Select columns...", size=14)
                self.selected_columns_container.controls.append(placeholder)

        self.page.update()

    def _create_limit_controls(self) -> ft.Row:
        """Create the controls for the result limit section."""
        self.limit_input = DpdTextField(
            name="result_limit",
            multiline=False,
            on_submit=self._apply_filters_clicked,
        )
        self.limit_input.hint_text = "0 for all results"
        self.limit_input.hint_style = ft.TextStyle(color=LABEL_COLOUR, size=10)
        self.limit_input.width = 200
        self.limit_input.value = "50"
        return ft.Row([self.limit_input])

    def _create_preset_controls(self) -> ft.Row:
        """Create the controls for the filter presets section."""
        # Preset dropdown
        preset_names = self.toolkit.filter_presets_manager.list_presets()
        self.preset_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(name) for name in preset_names],
            width=500,
            on_change=self._on_preset_selected,
        )

        # Set first preset as default if available
        if preset_names:
            self.preset_dropdown.value = preset_names[0]

        # Save preset button
        self.save_preset_button = ft.ElevatedButton(
            "Save",
            on_click=self._save_preset_clicked,
            width=80,
        )

        # Delete preset button
        self.delete_preset_button = ft.ElevatedButton(
            "Delete",
            on_click=self._delete_preset_clicked,
            width=80,
            disabled=len(preset_names) == 0,  # Disable if no presets
        )

        return ft.Row(
            [
                self.preset_dropdown,
                self.save_preset_button,
                self.delete_preset_button,
            ]
        )

    def _apply_filters_clicked(self, e: ft.ControlEvent | None) -> None:
        """Handle the Apply Filters button click."""
        # Refresh the database session to get the latest data
        self.toolkit.db_manager.new_db_session()

        data_filters = []
        for i, (column_dropdown, regex_input) in enumerate(
            zip(self.column_dropdowns, self.regex_inputs)
        ):
            if column_dropdown.value:  # Only check if column is selected
                data_filters.append((column_dropdown.value, regex_input.value or ""))

        display_filters = []
        for checkbox in self.column_checkboxes:
            if checkbox.value:
                display_filters.append(str(checkbox.label))

        limit = 0
        if self.limit_input and self.limit_input.value:
            try:
                limit = int(self.limit_input.value)
            except ValueError:
                limit = 0

        new_filter_component = FilterComponent(
            page=self.page,
            toolkit=self.toolkit,
            data_filters=data_filters,
            display_filters=display_filters,
            limit=limit,
        )

        self.filter_component_container.content = new_filter_component
        self.page.update()

    def _clear_filters_clicked(self, e: ft.ControlEvent | None) -> None:
        """Handle the Clear Filters button click."""
        # Clear only the regex input fields, not the dropdown selections
        for regex_input in self.regex_inputs:
            regex_input.value = ""

        # Clear limit input
        if self.limit_input:
            self.limit_input.value = "50"

        # Clear the filter component container
        self.filter_component_container.content = ft.Column([])
        self.page.update()

    def _on_preset_selected(self, e: ft.ControlEvent) -> None:
        """Handle preset selection from dropdown."""
        if self.preset_dropdown and self.preset_dropdown.value:
            preset_name = self.preset_dropdown.value
            preset_data = self.toolkit.filter_presets_manager.get_preset(preset_name)

            if preset_data and isinstance(preset_data, dict):
                # Load preset data into current filters
                data_filters = preset_data.get("data_filters", [])
                display_filters = preset_data.get("display_filters", [])
                limit = preset_data.get("limit", 50)

                # Update data filters - ensure proper types
                if isinstance(data_filters, list):
                    # Clear existing filter rows beyond the first one
                    while len(self.filter_rows) > 1:
                        # Remove from UI
                        if self.data_filters_container and self.filter_rows[1:]:
                            self.data_filters_container.controls.remove(
                                self.filter_rows[-1]
                            )
                        # Remove from lists
                        self.filter_rows.pop()
                        self.column_dropdowns.pop()
                        self.regex_inputs.pop()

                    # Ensure we have enough filter rows for the data
                    while len(self.column_dropdowns) < len(data_filters):
                        self._add_filter_row(None)

                    # Update existing filter rows
                    for i, item in enumerate(data_filters):
                        if isinstance(item, (list, tuple)) and len(item) >= 1:
                            column = item[0]
                            value = item[1] if len(item) > 1 else ""
                            if (
                                isinstance(column, str)
                                and isinstance(value, str)
                                and i < len(self.column_dropdowns)
                            ):
                                self.column_dropdowns[i].value = column
                                self.regex_inputs[i].value = value

                # Update display filters - ensure proper types
                if isinstance(display_filters, list):
                    for checkbox in self.column_checkboxes:
                        if checkbox.label and isinstance(checkbox.label, str):
                            checkbox.value = checkbox.label in display_filters
                    self._on_column_checkbox_change(None)

                # Update limit - ensure proper type
                if isinstance(limit, int) and self.limit_input:
                    self.limit_input.value = str(limit)
                elif self.limit_input:
                    self.limit_input.value = "50"

                self.page.update()

    def _save_preset_clicked(self, e: ft.ControlEvent) -> None:
        """Handle save preset button click."""
        # Get current filter values
        data_filters = []
        for i, (column_dropdown, regex_input) in enumerate(
            zip(self.column_dropdowns, self.regex_inputs)
        ):
            if column_dropdown.value:
                # Save only the column name if no value is provided
                if regex_input.value:
                    data_filters.append([column_dropdown.value, regex_input.value])
                else:
                    data_filters.append([column_dropdown.value])

        display_filters = []
        for checkbox in self.column_checkboxes:
            if checkbox.value:
                display_filters.append(str(checkbox.label))

        limit = DEFAULT_LIMIT
        if self.limit_input and self.limit_input.value:
            try:
                limit = int(self.limit_input.value)
            except ValueError:
                limit = DEFAULT_LIMIT

        # Show input dialog for preset name
        name_field = ft.TextField(label="Preset Name", autofocus=True)

        def on_save_click(e: ft.ControlEvent) -> None:
            preset_name = name_field.value.strip() if name_field.value else ""
            if preset_name:
                self.toolkit.filter_presets_manager.save_preset(
                    preset_name, data_filters, display_filters, limit
                )

                # Update dropdown options
                if self.preset_dropdown:
                    preset_names = self.toolkit.filter_presets_manager.list_presets()
                    self.preset_dropdown.options = [
                        ft.dropdown.Option(name) for name in preset_names
                    ]
                    self.preset_dropdown.value = preset_name

                # Enable delete button if it was disabled
                if self.delete_preset_button:
                    self.delete_preset_button.disabled = False

                # Close the dialog
                self.page.close(name_dialog)

                # Refresh the UI to show the newly saved preset
                self.page.update()

        def on_cancel_click(e: ft.ControlEvent) -> None:
            self.page.close(name_dialog)

        name_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Save Filter Preset"),
            content=name_field,
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel_click),
                ft.TextButton("Save", on_click=on_save_click),
            ],
        )

        self.page.open(name_dialog)
        self.page.update()

    def _delete_preset_clicked(self, e: ft.ControlEvent) -> None:
        """Handle delete preset button click."""
        if not self.preset_dropdown or not self.preset_dropdown.value:
            return

        preset_name = self.preset_dropdown.value

        def on_delete_click(e: ft.ControlEvent) -> None:
            # Delete the preset
            self.toolkit.filter_presets_manager.delete_preset(preset_name)

            # Update dropdown options
            if self.preset_dropdown:
                preset_names = self.toolkit.filter_presets_manager.list_presets()
                self.preset_dropdown.options = [
                    ft.dropdown.Option(name) for name in preset_names
                ]

                # Select first preset or None
                self.preset_dropdown.value = preset_names[0] if preset_names else None

                # Disable delete button if no presets left
                if self.delete_preset_button:
                    self.delete_preset_button.disabled = len(preset_names) == 0

            # Refresh the UI to show the updated preset list before closing dialog
            self.page.update()

            # Close the dialog
            self.page.close(delete_dialog)

            # Final page update after closing dialog
            self.page.update()

        def on_cancel_delete(e: ft.ControlEvent) -> None:
            self.page.close(delete_dialog)

        # Show confirmation dialog
        delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Filter Preset"),
            content=ft.Text(
                f"Are you sure you want to delete the preset '{preset_name}'?"
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel_delete),
                ft.TextButton("Delete", on_click=on_delete_click),
            ],
        )

        self.page.open(delete_dialog)
        self.page.update()

    def _reset_to_default_clicked(self, e: ft.ControlEvent | None) -> None:
        """Handle the Reset to Default button click."""
        # Load the first preset as default if available
        first_preset_data = self.toolkit.filter_presets_manager.get_first_preset()

        if first_preset_data:
            # Load preset data into current filters
            data_filters = first_preset_data.get("data_filters", [])
            display_filters = first_preset_data.get("display_filters", [])
            limit = first_preset_data.get("limit", DEFAULT_LIMIT)

            # Update data filters - ensure proper types
            if isinstance(data_filters, list):
                for i, item in enumerate(data_filters):
                    if isinstance(item, (list, tuple)) and len(item) >= 1:
                        column = item[0]
                        value = item[1] if len(item) > 1 else ""
                        if i < len(self.column_dropdowns):
                            self.column_dropdowns[i].value = column
                            self.regex_inputs[i].value = value

                # Add more filter rows if needed
                for i in range(len(data_filters) - len(self.column_dropdowns)):
                    self._add_filter_row(None)

            # Update display filters - ensure proper types
            if isinstance(display_filters, list):
                for checkbox in self.column_checkboxes:
                    if checkbox.label and isinstance(checkbox.label, str):
                        checkbox.value = checkbox.label in display_filters
                self._on_column_checkbox_change(None)

            # Update limit - ensure proper type
            if isinstance(limit, int) and self.limit_input:
                self.limit_input.value = str(limit)
        else:
            # Fallback to original hardwired values if no presets exist
            default_data_filters = [("root_key", ""), ("family_root", "")]

            # Reset display filters to default values
            default_display_filters = [
                "id",
                "lemma_1",
                "meaning_1",
                "meaning_lit",
                "root_key",
                "family_root",
            ]

            # Reset limit to default
            default_limit = 50

            # Re-initialize filters with default values
            self._initialize_filters(
                data_filters=default_data_filters,
                display_filters=default_display_filters,
                limit=default_limit,
            )

        # Clear the filter component container
        self.filter_component_container.content = ft.Column([])
        self.page.update()
