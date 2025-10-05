from typing import Optional

import flet as ft

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=LABEL_COLOUR, size=10)


class WordFinderWidget:
    def __init__(self, toolkit, initial_word: Optional[str] = None):
        self.toolkit = toolkit
        self.wordfinder = toolkit.wordfinder_manager
        self.initial_word = initial_word

        # UI elements

        self.label = ft.Text(
            "wordfinder",
            color=ft.Colors.GREY_500,
            width=150,
            size=12,
        )

        self.search_field = ft.TextField(
            autofocus=True,
            text_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            label="Wordfinder",
            label_style=TEXT_FIELD_LABEL_STYLE,
            value=self.initial_word or "",
            width=300,
            on_submit=self.clicked_search,
            border_radius=20,
        )

        self.search_button = ft.ElevatedButton(
            text="Search",
            on_click=self.clicked_search,
        )

        self.clear_button = ft.ElevatedButton(
            text="Clear",
            on_click=self.clear_wordfinder_results,
        )

        self.search_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("EXACT"),
                ft.dropdown.Option("STARTS_WITH"),
                ft.dropdown.Option("CONTAINS"),
                ft.dropdown.Option("REGEX"),
            ],
            value="STARTS_WITH",  # Default
            label="Search Type",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=300,
            text_size=10,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
        )

        self.results_container = ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            visible=False,
            padding=10,
            border_radius=20,
            width=1350,
            height=150,
        )

        # Main widget
        self.widget = ft.Column(
            [
                ft.Row(
                    [
                        # self.label,
                        self.search_field,
                        self.search_button,
                        self.clear_button,
                        self.search_type_dropdown,
                    ],
                    spacing=10,
                ),
                self.results_container,
            ],
            spacing=10,
        )

    def get_widget(self) -> ft.Column:
        return self.widget

    def clicked_search(self, e):
        word = (self.search_field.value or "").strip()
        search_type = self.search_type_dropdown.value
        if not word:
            self.show_error("Please enter a word to search.")
            return

        try:
            self.wordfinder.search_for(word, search_type, printer=False)
            results = (
                self.wordfinder.search_results
            )  # Get raw results to format manually
            if results:
                # Create DataTable with headers and data rows
                data_table = ft.DataTable(
                    border=ft.border.all(1, HIGHLIGHT_COLOUR),
                    border_radius=10,
                    heading_row_color=ft.Colors.GREY_800,
                    data_row_color={ft.ControlState.HOVERED: ft.Colors.GREY_700},
                    column_spacing=10,
                    heading_row_height=40,
                    columns=[
                        ft.DataColumn(ft.Text("Book", color=ft.Colors.WHITE)),
                        ft.DataColumn(ft.Text("Word", color=ft.Colors.WHITE)),
                        ft.DataColumn(ft.Text("Freq", color=ft.Colors.WHITE)),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(
                                    ft.Text(
                                        book, color=ft.Colors.WHITE, selectable=True
                                    )
                                ),
                                ft.DataCell(
                                    ft.Text(
                                        word, color=ft.Colors.WHITE, selectable=True
                                    )
                                ),
                                ft.DataCell(
                                    ft.Text(
                                        str(freq),
                                        color=ft.Colors.WHITE,
                                        selectable=True,
                                    )
                                ),
                            ],
                        )
                        for book, word, freq in results
                    ],
                )

                self.results_container.content = ft.Column(
                    [data_table],
                    scroll=ft.ScrollMode.AUTO,
                )
                self.results_container.visible = True
                self.widget.update()
                self.toolkit.page.update()
            else:
                self.show_error("No results found.")
        except Exception as ex:
            self.show_error(f"Search error: {str(ex)}")

    def clear_wordfinder_results(self, e):
        self.results_container.visible = False
        self.results_container.content = ft.Column(
            [],
            scroll=ft.ScrollMode.AUTO,
        )
        self.widget.update()
        self.toolkit.page.update()

    def show_error(self, message: str):
        self.results_container.content = ft.Column(
            [
                ft.Text(
                    message,
                    color=ft.Colors.RED,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        self.results_container.visible = True
        self.widget.update()
        self.toolkit.page.update()
