from typing import List

import flet as ft

from db.models import DpdHeadword
from gui2.dpd_fields_classes import DpdDropdown, DpdTextField
from gui2.filter_component import FilterComponent
from gui2.toolkit import ToolKit

LABEL_COLOUR = ft.Colors.GREY_500


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
        limit: int = 10,
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

        self.filter_component_container = ft.Container(
            content=ft.Column([], expand=True, scroll=ft.ScrollMode.AUTO),
            expand=True,
        )

        self._build_ui()
        self._initialize_filters(data_filters, display_filters, limit)

    def _initialize_filters(
        self,
        data_filters: List[tuple[str, str]] | None = None,
        display_filters: List[str] | None = None,
        limit: int | None = None,
    ):
        """Initialize the filter with predefined values."""
        if data_filters:
            for i in range(len(data_filters) - len(self.column_dropdowns)):
                self._add_filter_row(None)

            for i, (column, value) in enumerate(data_filters):
                if i < len(self.column_dropdowns):
                    self.column_dropdowns[i].value = column
                    self.regex_inputs[i].value = value

        if display_filters:
            for checkbox in self.column_checkboxes:
                checkbox.value = checkbox.label in display_filters
            self._on_column_checkbox_change(None)

        if limit is not None and self.limit_input:
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
        buttons_section = ft.Row(
            [
                ft.Container(
                    ft.Text("Filters", size=14, color=LABEL_COLOUR),
                    width=150,
                ),
                apply_button,
                clear_button,
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
                    bgcolor=ft.Colors.BLUE_GREY_500,
                    border_radius=12,
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
        )
        self.limit_input.hint_text = "0 for all results"
        self.limit_input.hint_style = ft.TextStyle(color=LABEL_COLOUR, size=10)
        self.limit_input.width = 200
        self.limit_input.value = "20"
        return ft.Row([self.limit_input])

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
            self.limit_input.value = "10"

        # Clear the filter component container
        self.filter_component_container.content = ft.Column([])
        self.page.update()
