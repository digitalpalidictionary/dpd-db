from typing import TypedDict

import flet as ft

from db_tests.db_tests_manager import InternalTestRow
from gui2.filter_component import FilterComponent
from gui2.tests_tab_controller import TestsTabController
from gui2.toolkit import ToolKit
from gui2.ui_utils import show_global_snackbar

LOGIC_OPTIONS: list[str] = [
    "equals",
    "does not equal",
    "contains",
    "contains word",
    "does not contain",
    "does not contain word",
    "is empty",
    "is not empty",
]

# Constants for styling
LABEL_WIDTH = 100
COLUMN_WIDTH = 300
LABEL_COLOUR = ft.Colors.GREY_500
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=LABEL_COLOUR, size=10)
LIGHT_BLUE = ft.Colors.BLUE_200


class TestElements(TypedDict):
    label: ft.Text
    search_column: ft.Dropdown
    search_sign: ft.Dropdown
    search_string: ft.TextField


class TestsTabView(ft.Column):
    def __init__(self, page: ft.Page, toolkit: ToolKit):
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=0,
        )
        self.page: ft.Page = page
        self.toolkit = toolkit

        # Get DpdHeadword column names for dropdown options
        from db.models import DpdHeadword

        self.dpd_column_names: list[str] = [
            column.name for column in DpdHeadword.__table__.columns
        ]
        self.dpd_column_options: list[ft.dropdown.Option] = [
            ft.dropdown.Option(name) for name in self.dpd_column_names
        ]

        # Instantiate the controller after all UI elements are defined
        self.controller = TestsTabController(self, toolkit)

        # --- Define UI Elements as Instance Attributes ---

        # Row 1 Elements
        self.run_tests_button = ft.ElevatedButton(
            "Run Tests",
            key="test_db_internal",
            tooltip="Run internal database tests",
            on_click=self.controller.handle_run_tests_clicked,
            height=50,
            width=150,
        )
        self.test_direction_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            tooltip="Toggle test direction",
            on_click=self.controller.handle_toggle_test_direction,
        )
        self.stop_tests_button = ft.ElevatedButton(
            "Stop Tests",
            key="test_stop",
            tooltip="Stop ongoing tests",
            on_click=self.controller.handle_stop_tests_clicked,
            height=50,
            width=150,
        )
        self.edit_tests_button = ft.ElevatedButton(
            "Edit Tests",
            key="test_edit",
            tooltip="Open tests file for editing",
            on_click=self.controller.handle_edit_tests_clicked,
            height=50,
            width=150,
        )
        self.update_tests_button = ft.ElevatedButton(
            "Update Test",
            key="test_update",
            on_click=self.controller.handle_test_update,
            height=50,
            width=150,
        )
        self.add_new_test_button = ft.ElevatedButton(
            "Add New Test",
            key="test_new",
            on_click=self.controller.handle_add_new_test,
            height=50,
            width=150,
        )
        self.delete_test_button = ft.ElevatedButton(
            "Delete Test",
            key="test_delete",
            on_click=self.controller.handle_delete_test,
            height=50,
            width=150,
        )

        # Row 2 Elements
        self.test_number_text = ft.Text(
            "0",
            key="test_number",
            width=LABEL_WIDTH,
            text_align=ft.TextAlign.RIGHT,
        )
        self.test_name_input = ft.TextField(
            label="",
            key="test_name",
            width=900 + 10 - 100,
            label_style=TEXT_FIELD_LABEL_STYLE,
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
        )
        self.iterations_input = ft.TextField(
            label="Iter",
            key="iterations",
            width=100,
            label_style=TEXT_FIELD_LABEL_STYLE,
        )

        # Rows 3-8: Test Criteria Elements
        self.search_criteria_elements: list[TestElements] = []
        for i in range(6):
            elements: TestElements = {
                "label": ft.Text(
                    f"test {i + 1}",
                    key=f"test_label_{i + 1}",
                    width=LABEL_WIDTH,
                    text_align=ft.TextAlign.RIGHT,
                    color=LABEL_COLOUR,
                ),
                "search_column": ft.Dropdown(
                    label="",
                    key=f"search_column_{i + 1}",
                    width=COLUMN_WIDTH,
                    label_style=TEXT_FIELD_LABEL_STYLE,
                    options=self.dpd_column_options,
                    editable=True,
                    enable_filter=True,
                    enable_search=True,
                    menu_height=300,
                ),
                "search_sign": ft.Dropdown(
                    label="",
                    key=f"search_sign_{i + 1}",
                    width=COLUMN_WIDTH,
                    options=[ft.dropdown.Option(logic) for logic in LOGIC_OPTIONS],
                    label_style=TEXT_FIELD_LABEL_STYLE,
                ),
                "search_string": ft.TextField(
                    label="",
                    key=f"search_string_{i + 1}",
                    width=COLUMN_WIDTH,
                    label_style=TEXT_FIELD_LABEL_STYLE,
                ),
            }
            self.search_criteria_elements.append(elements)

        # Row 9 Elements
        self.display_1_input = ft.Dropdown(
            label="",
            key="display_1",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            options=self.dpd_column_options,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=300,
        )
        self.display_2_input = ft.Dropdown(
            label="",
            key="display_2",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            options=self.dpd_column_options,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=300,
        )
        self.display_3_input = ft.Dropdown(
            label="",
            key="display_3",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            options=self.dpd_column_options,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=300,
        )

        # Row 10 Elements
        self.error_column_input = ft.Dropdown(
            label="Error Column",
            key="error_column",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            options=self.dpd_column_options,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=300,
        )
        self.exceptions_textfield = ft.TextField(
            label="Exceptions",
            key="exceptions",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            read_only=True,
        )
        self.test_add_exception_dropdown = ft.Dropdown(
            label="Add Exception",
            key="test_add_exception",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            options=[],
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=200,
        )
        self.test_add_exception_button = ft.ElevatedButton(
            "Add 1",
            key="test_add_exception_button",
            on_click=self.controller.handle_add_exception_button,
        )
        self.test_add_all_exceptions_button = ft.ElevatedButton(
            "Add All",
            key="test_add_all_exceptions_button",
            on_click=self.controller.handle_add_all_exceptions_clicked,
        )

        # Row 11 Elements
        self.test_rerun_button = ft.ElevatedButton(
            "Rerun",
            key="test_rerun",
            width=150,
            height=50,
            on_click=self.controller.handle_rerun_test_clicked,
        )
        self.test_next_button = ft.ElevatedButton(
            "Next",
            key="test_next",
            expand=True,
            height=50,
            on_click=self.controller.handle_next_test_clicked,
        )

        # Row 12 Elements
        self.test_results_redux_text = ft.Text(
            "0",
            key="test_results_redux",
            color=ft.Colors.WHITE,
        )
        self.test_results_total_text = ft.Text(
            "0",
            key="test_results_total",
            color=ft.Colors.WHITE,
        )
        self.test_db_query_input = ft.TextField(
            label="DB Browser Query",
            key="test_db_query",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            text_size=12,
        )
        self.test_db_query_copy_button = ft.IconButton(
            icon=ft.Icons.COPY,
            key="test_db_query_copy",
            tooltip="Copy DB Browser Query",
            on_click=self.controller.handle_test_db_query_copy,
        )

        # Row 13 Elements
        self.filter_component_container = ft.Container(
            content=ft.Column([], expand=True),
            expand=True,
        )

        # --- Construct Rows and Add to self.controls ---

        spacer_row = ft.Row(height=10)

        # Row 1: Buttons
        row_start_stop_edit = ft.Row(
            controls=[
                self.run_tests_button,
                self.test_direction_button,
                self.stop_tests_button,
                self.edit_tests_button,
                ft.Container(width=25),  # Spacer
                self.update_tests_button,
                self.add_new_test_button,
                self.delete_test_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        # Row 2: Test Info
        row_test_name_etc = ft.Row(
            controls=[
                self.test_number_text,
                self.test_name_input,
                self.iterations_input,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Rows 3-8: Test Criteria
        rows_test_criteria = []
        for i in range(6):
            elements = self.search_criteria_elements[i]
            row = ft.Row(
                controls=[
                    elements["label"],
                    elements["search_column"],
                    elements["search_sign"],
                    elements["search_string"],
                ],
                alignment=ft.MainAxisAlignment.START,
            )
            rows_test_criteria.append(row)

        # Row 9: Display Fields
        row_display = ft.Row(
            controls=[
                ft.Text(
                    "display",
                    width=LABEL_WIDTH,
                    text_align=ft.TextAlign.RIGHT,
                    color=LABEL_COLOUR,
                ),
                self.display_1_input,
                self.display_2_input,
                self.display_3_input,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 10: Error Info
        row_commentary_exceptions = ft.Row(
            controls=[
                ft.Text(
                    "",
                    width=LABEL_WIDTH,
                    text_align=ft.TextAlign.RIGHT,
                    color=LABEL_COLOUR,
                ),
                self.error_column_input,
                self.exceptions_textfield,
                self.test_add_exception_dropdown,
                self.test_add_exception_button,
                self.test_add_all_exceptions_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 11: Navigation Buttons
        row_next_button = ft.Row(
            controls=[
                self.test_rerun_button,
                self.test_next_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 12: Results Summary
        row_test_results = ft.Row(
            controls=[
                ft.Text("displaying", color=LIGHT_BLUE),
                self.test_results_redux_text,
                ft.Text("of", color=LIGHT_BLUE),
                self.test_results_total_text,
                ft.Text("results", color=LIGHT_BLUE),
                ft.Container(width=250),  # space
                self.test_db_query_input,
                self.test_db_query_copy_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 13: Results Table
        row_datatable = ft.Row(
            controls=[
                self.filter_component_container,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # Add all rows to the Column's controls
        self.controls.extend(
            [
                spacer_row,
                row_start_stop_edit,
                ft.Divider(),
                row_test_name_etc,
                *rows_test_criteria,
                row_display,
                row_commentary_exceptions,
                ft.Divider(),
                row_next_button,
                ft.Divider(),
                row_test_results,
                row_datatable,
                ft.Divider(),
                row_next_button,
            ]
        )

    def update_test_name(self, text: str):
        self.test_name_input.value = text
        self.page.update()

    def set_run_tests_button_disabled_state(self, disabled: bool):
        self.run_tests_button.disabled = disabled
        self.page.update()

    def set_stop_tests_button_disabled_state(self, disabled: bool):
        self.stop_tests_button.disabled = disabled
        self.page.update()

    def update_test_number_display(self, test_number: str):
        self.test_number_text.value = test_number
        self.page.update()

    def clear_all_fields(self):
        """Clears all input fields and resets test results in the view."""
        self.test_name_input.value = ""
        self.iterations_input.value = ""

        for elements in self.search_criteria_elements:
            elements["search_column"].value = None  # Clears dropdown selection
            elements["search_sign"].value = None  # Clears dropdown selection
            elements["search_string"].value = ""

        self.display_1_input.value = None  # Clears dropdown selection
        self.display_2_input.value = None  # Clears dropdown selection
        self.display_3_input.value = None  # Clears dropdown selection

        self.error_column_input.value = None  # Clears dropdown selection
        self.exceptions_textfield.value = ""

        self.test_add_exception_dropdown.value = None  # Clears dropdown selection
        # self.test_add_exception_dropdown.options = [] # Optionally clear options

        self.test_db_query_input.value = ""

        # Reset text displays
        self.test_number_text.value = "0"
        self.test_results_redux_text.value = "0"
        self.test_results_total_text.value = "0"

        # Clear results table
        # Results table is now handled by filter component
        self.set_filter_component(None)

        self.reset_field_highlights()

        self.page.update()

    def update_results_summary_display(self, displayed_count: int, total_found: int):
        self.test_results_redux_text.value = str(displayed_count)
        self.test_results_total_text.value = str(total_found)
        self.page.update()

    def update_datatable_columns(self, test_definition: InternalTestRow | None):
        # This method is no longer needed as the filter component handles column display
        pass

    def populate_with_test_definition(self, test_def: InternalTestRow):
        """Populates the view's input fields with data from the test definition."""
        self.iterations_input.value = str(test_def.iterations)

        # Populate search criteria fields
        for i in range(6):
            if i < len(self.search_criteria_elements):
                view_elements = self.search_criteria_elements[i]
                # For dropdowns, set .value to the string value from test_def.
                # If the value is not in the options, Flet will handle it (likely show empty or allow custom input due to editable=True).
                search_column_value = getattr(test_def, f"search_column_{i + 1}", "")
                view_elements["search_column"].value = (
                    search_column_value if search_column_value else None
                )
                # Ensure the value for dropdown is one of its options or None
                sign_value = getattr(test_def, f"search_sign_{i + 1}", "")
                if view_elements["search_sign"].options and sign_value in [
                    opt.key for opt in view_elements["search_sign"].options
                ]:
                    view_elements["search_sign"].value = sign_value
                else:
                    view_elements[
                        "search_sign"
                    ].value = None  # Or a default valid option
                view_elements["search_string"].value = getattr(
                    test_def, f"search_string_{i + 1}", ""
                )

        # For dropdowns, set .value to the string value from test_def.
        # If the value is not in the options, Flet will handle it.
        self.display_1_input.value = test_def.display_1 if test_def.display_1 else None
        self.display_2_input.value = test_def.display_2 if test_def.display_2 else None
        self.display_3_input.value = test_def.display_3 if test_def.display_3 else None
        self.error_column_input.value = (
            test_def.error_column if test_def.error_column else None
        )
        self.exceptions_textfield.value = (
            ", ".join(map(str, sorted(test_def.exceptions)))
            if test_def.exceptions
            else ""
        )
        self.page.update()

    def set_filter_component(self, filter_component: FilterComponent | None) -> None:
        self.filter_component_container.content = filter_component
        self.page.update()

    def show_snackbar(self, message: str, color: str = ft.Colors.BLUE_100) -> None:
        """Show a snackbar message."""
        show_global_snackbar(self.page, message, "info", 3000)

    def highlight_invalid_field(self, field_name: str):
        """Highlights the specified field with a red border."""
        try:
            # e.g. "search_column_2" -> "search_column", "2"
            base_name, index_str = field_name.rsplit("_", 1)
            index = int(index_str) - 1

            if 0 <= index < len(self.search_criteria_elements):
                elements = self.search_criteria_elements[index]
                if base_name in elements:
                    control = elements[base_name]
                    control.border_color = ft.Colors.RED
                    self.page.update()
        except (ValueError, KeyError) as e:
            print(f"Error highlighting field '{field_name}': {e}")

    def reset_field_highlights(self):
        """Resets the border color of all fields."""
        for elements in self.search_criteria_elements:
            for control in elements.values():
                if isinstance(control, (ft.Dropdown, ft.TextField)):
                    control.border_color = None
        self.page.update()
