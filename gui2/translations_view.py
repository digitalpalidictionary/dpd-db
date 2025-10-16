import re

import flet as ft

from gui2.toolkit import ToolKit
from tools.pali_text_files import cst_texts
from tools.tipitaka_db import search_all_cst_texts, search_book

# Style constants from pass1_auto_view.py
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=ft.Colors.GREY_500, size=10)


class TranslationsView(ft.Column):
    def __init__(self, page: ft.Page, toolkit: ToolKit):
        super().__init__(expand=True, spacing=10)
        self.page = page
        self.toolkit = toolkit

        # --- UI Controls ---
        self.search_term_field = ft.TextField(
            label="Regex to search for",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=400,
            on_submit=self.search_clicked,
            border_radius=20,
            border_color=ft.Colors.BLUE_200,
        )

        book_options = ["all"]
        book_options.extend(cst_texts.keys())
        self.books_dropdown = ft.Dropdown(
            label="Book",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=300,
            options=[ft.dropdown.Option(key) for key in book_options],
            value="all",
            text_size=14,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
        )

        self.search_button = ft.ElevatedButton(
            "Search", on_click=self.search_clicked, width=120
        )
        self.clear_button = ft.ElevatedButton(
            "Clear", on_click=self.clear_clicked, width=120
        )

        self.results_column = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )

        self.results_container = ft.Container(
            content=self.results_column,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=ft.border_radius.all(20),
            padding=10,
            expand=True,
            visible=False,  # Initially invisible
        )

        # --- Build UI by adding to self.controls ---
        root_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.search_term_field,
                            self.books_dropdown,
                            self.search_button,
                            self.clear_button,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    self.results_container,
                ],
                expand=True,
            ),
            padding=ft.Padding(0, 10, 0, 0),  # Add top padding
            expand=True,
        )

        self.controls.append(root_container)

    def search_clicked(self, e):
        search_term = self.search_term_field.value

        if not search_term:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Please enter a search term."), open=True
            )
            self.page.update()
            return

        book = self.books_dropdown.value

        # --- Start of search: show progress ring with no border ---
        self.results_container.visible = True
        self.results_container.border = None  # Hide border during loading
        self.results_column.controls.clear()
        self.results_column.controls.append(
            ft.Row([ft.ProgressRing()], alignment=ft.MainAxisAlignment.CENTER)
        )
        self.page.update()

        # --- Perform search ---
        book = self.books_dropdown.value
        if book == "all":
            results = search_all_cst_texts(search_term)
        else:
            results = search_book(book, search_term)

        # --- After search: restore border and show results ---
        self.results_container.border = ft.border.all(
            1, ft.Colors.BLUE_200
        )  # Restore border
        self.results_column.controls.clear()

        if not results:
            self.results_column.controls.append(ft.Text("No results found."))
        else:
            total_results = len(results)
            display_limit = 50
            results_to_display = results[:display_limit]

            if total_results > display_limit:
                count_message = (
                    f"Found {total_results} results, displaying first {display_limit}."
                )
            else:
                count_message = f"Found {total_results} results."

            self.results_column.controls.append(ft.Text(count_message))

            for pali_text, eng_trans, table_name, book_name in results_to_display:
                pali_text_lower = pali_text.lower()

                text_spans = []
                last_end = 0

                try:
                    # Find all matches of the regex, case-insensitively
                    for match in re.finditer(
                        search_term, pali_text_lower, re.IGNORECASE
                    ):
                        start, end = match.span()
                        # Add the part before the match
                        text_spans.append(ft.TextSpan(pali_text_lower[last_end:start]))
                        # Add the highlighted match
                        text_spans.append(
                            ft.TextSpan(
                                pali_text_lower[start:end],
                                ft.TextStyle(
                                    color=ft.Colors.BLACK, bgcolor=ft.Colors.YELLOW_200
                                ),
                            )
                        )
                        last_end = end

                    # Add the remaining part of the text
                    text_spans.append(ft.TextSpan(pali_text_lower[last_end:]))

                except re.error as e:
                    # Handle invalid regex by not highlighting and showing an error
                    text_spans = [
                        ft.TextSpan(
                            f"Invalid Regex: {e}\n\n",
                            style=ft.TextStyle(color=ft.Colors.RED),
                        ),
                        ft.TextSpan(pali_text_lower),
                    ]

                result_card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"Book: {book_name}, Table: {table_name}",
                                    theme_style=ft.TextThemeStyle.LABEL_SMALL,
                                    color=ft.Colors.SECONDARY,
                                    selectable=True,
                                ),
                                ft.Text(spans=text_spans, selectable=True),
                                ft.Divider(height=5, color="transparent"),
                                ft.Text(
                                    eng_trans, selectable=True, color=ft.Colors.GREY_700
                                ),
                            ]
                        ),
                    )
                )
                self.results_column.controls.append(result_card)

        self.page.update()

    def clear_clicked(self, e):
        self.search_term_field.value = ""
        self.results_column.controls.clear()
        self.results_container.visible = False  # Hide container on clear
        self.page.update()
