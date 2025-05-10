import flet as ft
from gui2.toolkit import ToolKit

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


class TestsTabView(ft.Column):
    def __init__(self, page: ft.Page, toolkit: ToolKit):
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=0,
        )
        self.page = page
        self.toolkit = toolkit

        # --- Define UI Elements as Instance Attributes ---

        # Row 1 Elements
        self.run_tests_button = ft.ElevatedButton(
            "Run Tests",
            key="test_db_internal",
            tooltip="Run internal database tests",
        )
        self.stop_tests_button = ft.ElevatedButton(
            "Stop Tests",
            key="test_stop",
            tooltip="Stop ongoing tests",
        )
        self.edit_tests_button = ft.ElevatedButton(
            "Edit Tests",
            key="test_edit",
            tooltip="Open tests file for editing",
        )

        # Row 2 Elements
        self.test_number_text = ft.Text(
            "0",
            key="test_number",
            width=LABEL_WIDTH,
            text_align=ft.TextAlign.RIGHT,
        )
        self.test_name_input = ft.TextField(
            label="Test Name",
            key="test_name",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            text_style=ft.TextStyle(color=ft.colors.WHITE),
        )
        self.iterations_input = ft.TextField(
            label="Iter",
            key="iterations",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
        )

        # Rows 3-8: Test Criteria Elements
        self.search_criteria_elements: list[dict[str, ft.Control]] = []
        for i in range(6):
            elements = {
                "label": ft.Text(
                    f"test {i + 1}",
                    key=f"test_label_{i + 1}",
                    width=LABEL_WIDTH,
                    text_align=ft.TextAlign.RIGHT,
                    color=LABEL_COLOUR,
                ),
                "search_column": ft.TextField(
                    label="Search Column",
                    key=f"search_column_{i + 1}",
                    width=COLUMN_WIDTH,
                    label_style=TEXT_FIELD_LABEL_STYLE,
                ),
                "search_sign": ft.Dropdown(
                    label="Logic",
                    key=f"search_sign_{i + 1}",
                    width=COLUMN_WIDTH,
                    options=[ft.dropdown.Option(logic) for logic in LOGIC_OPTIONS],
                    label_style=TEXT_FIELD_LABEL_STYLE,
                ),
                "search_string": ft.TextField(
                    label="Search String",
                    key=f"search_string_{i + 1}",
                    width=COLUMN_WIDTH,
                    label_style=TEXT_FIELD_LABEL_STYLE,
                ),
            }
            self.search_criteria_elements.append(elements)

        # Row 9 Elements
        self.display_1_input = ft.TextField(
            label="Display 1",
            key="display_1",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
        )
        self.display_2_input = ft.TextField(
            label="Display 2",
            key="display_2",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
        )
        self.display_3_input = ft.TextField(
            label="Display 3",
            key="display_3",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
        )

        # Row 10 Elements
        self.error_column_input = ft.TextField(
            label="Error Column",
            key="error_column",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
        )
        self.exceptions_dropdown = ft.Dropdown(
            label="Exceptions",
            key="exceptions",
            width=COLUMN_WIDTH,
            options=[],  # Initially empty
            label_style=TEXT_FIELD_LABEL_STYLE,
        )

        # Row 11 Elements
        self.update_tests_button = ft.ElevatedButton("Update Tests", key="test_update")
        self.add_new_test_button = ft.ElevatedButton("Add New Test", key="test_new")
        self.delete_test_button = ft.ElevatedButton("Delete Test", key="test_delete")

        # Row 12 Elements
        self.test_results_redux_text = ft.Text(
            "0",
            key="test_results_redux",
            color=ft.colors.WHITE,
        )
        self.test_results_total_text = ft.Text(
            "0",
            key="test_results_total",
            color=ft.colors.WHITE,
        )

        # Row 13 Elements
        self.test_results_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("1")),
                ft.DataColumn(ft.Text("2")),
                ft.DataColumn(ft.Text("3")),
            ],
            rows=[],
        )

        # Row 14 Elements
        self.test_add_exception_dropdown = ft.Dropdown(
            label="Add Exception",
            key="test_add_exception",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
            options=[],
        )
        self.test_add_exception_button = ft.ElevatedButton(
            "Add",
            key="test_add_exception_button",
            width=COLUMN_WIDTH,
        )
        self.test_db_query_input = ft.TextField(
            label="DB Query",
            key="test_db_query",
            width=COLUMN_WIDTH,
            label_style=TEXT_FIELD_LABEL_STYLE,
        )
        self.test_db_query_copy_button = ft.IconButton(
            icon=ft.icons.COPY,
            key="test_db_query_copy",
            tooltip="Copy DB Query",
        )

        # Row 15 Elements
        self.test_next_button = ft.ElevatedButton(
            "Next",
            key="test_next",
            expand=True,
        )

        # --- Construct Rows and Add to self.controls ---

        # Row 1: Buttons
        row1 = ft.Row(
            controls=[
                ft.Container(width=LABEL_WIDTH),
                self.run_tests_button,
                self.stop_tests_button,
                self.edit_tests_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        # Row 2: Test Info
        row2 = ft.Row(
            controls=[
                self.test_number_text,
                self.test_name_input,
                self.iterations_input,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Rows 3-8: Test Criteria
        test_criteria_rows = []
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
            test_criteria_rows.append(row)

        # Row 9: Display Fields
        row9 = ft.Row(
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
        row10 = ft.Row(
            controls=[
                ft.Text(
                    "",
                    width=LABEL_WIDTH,
                    text_align=ft.TextAlign.RIGHT,
                    color=LABEL_COLOUR,
                ),
                self.error_column_input,
                self.exceptions_dropdown,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 11: Action Buttons
        row11 = ft.Row(
            controls=[
                ft.Container(width=LABEL_WIDTH),  # Spacer
                self.update_tests_button,
                self.add_new_test_button,
                self.delete_test_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 12: Results Summary
        row12 = ft.Row(
            controls=[
                ft.Container(width=LABEL_WIDTH),  # Spacer
                ft.Text("displaying", color=LIGHT_BLUE),
                self.test_results_redux_text,
                ft.Text("of", color=LIGHT_BLUE),
                self.test_results_total_text,
                ft.Text("results", color=LIGHT_BLUE),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 13: Results Table
        # self.test_results_table is already defined as an instance attribute
        row13 = ft.Row(
            controls=[
                ft.Text(
                    width=LABEL_WIDTH,
                    text_align=ft.TextAlign.RIGHT,
                    color=LABEL_COLOUR,
                ),
                ft.Container(  # To control size of DataTable
                    content=self.test_results_table,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    width=1000,
                    height=300,
                    expand=True,
                    alignment=ft.alignment.top_left,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # Row 14: Add Exception
        row14 = ft.Row(
            controls=[
                ft.Text(
                    width=LABEL_WIDTH,
                    text_align=ft.TextAlign.RIGHT,
                    color=LABEL_COLOUR,
                ),
                self.test_add_exception_dropdown,
                self.test_add_exception_button,
                self.test_db_query_input,
                self.test_db_query_copy_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Row 15: Next Button
        row15 = ft.Row(
            controls=[
                ft.Container(width=LABEL_WIDTH),  # Spacer
                self.test_next_button,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Add all rows to the Column's controls
        self.controls.extend(
            [
                row1,
                ft.Divider(),
                row2,
                *test_criteria_rows,
                row9,
                row10,
                ft.Divider(),
                row11,
                ft.Divider(),
                row12,
                row13,
                row14,
                row15,
            ]
        )
