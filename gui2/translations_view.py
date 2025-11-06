import re

import flet as ft

from gui2.toolkit import ToolKit
from tools.pali_text_files import cst_texts
from tools.tipitaka_db import search_all_cst_texts, search_book

# Style constants from pass1_auto_view.py
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=ft.Colors.GREY_500, size=10)
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class TranslationsView(ft.Column):
    def __init__(self, page: ft.Page, toolkit: ToolKit):
        super().__init__(expand=True, spacing=10)
        self.page: ft.Page = page
        self.toolkit = toolkit

        # --- UI Controls ---
        self.language_dropdown = ft.Dropdown(
            label="Language",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=150,
            options=[
                ft.dropdown.Option("Pāḷi"),
                ft.dropdown.Option("English"),
            ],
            value="Pāḷi",
            text_size=14,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            editable=True,
            enable_filter=True,
        )
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
            width=200,
            menu_width=200,
            menu_height=500,
            options=[ft.dropdown.Option(key) for key in book_options],
            value="all",
            text_size=14,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            editable=True,
            enable_filter=True,
        )

        self.search_button = ft.ElevatedButton(
            "Search", on_click=self.search_clicked, width=120
        )
        self.clear_button = ft.ElevatedButton(
            "Clear", on_click=self.clear_clicked, width=120
        )

        self.results_search_field = ft.TextField(
            label="Search in results",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=300,
            on_change=self.handle_text_search,
            border_radius=20,
            border_color=HIGHLIGHT_COLOUR,
        )

        self.results_column = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )

        self.results_container = ft.Container(
            content=self.results_column,
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
                            self.language_dropdown,
                            self.search_term_field,
                            self.books_dropdown,
                            self.search_button,
                            self.clear_button,
                            self.results_search_field,
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
        language = self.language_dropdown.value

        if not search_term:
            self.page.snack_bar = ft.SnackBar(  # type: ignore
                ft.Text("Please enter a search term."), open=True
            )
            self.page.update()
            return

        # Make search case-insensitive
        if not search_term.startswith("(?i)"):
            search_term = f"(?i){search_term}"

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
        results = []
        search_column = "pali_text" if language == "Pāḷi" else "english_translation"

        if book == "all":
            results = search_all_cst_texts(search_term, search_column=search_column)
        elif book:
            results = search_book(book, search_term, search_column=search_column)

        # --- After search: show results ---
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

                def get_highlighted_spans(text, term):
                    spans = []
                    last_end = 0
                    try:
                        for match in re.finditer(term, text, re.IGNORECASE):
                            start, end = match.span()
                            spans.append(ft.TextSpan(text[last_end:start]))
                            spans.append(
                                ft.TextSpan(
                                    text[start:end],
                                    ft.TextStyle(
                                        color=ft.Colors.BLACK,
                                        bgcolor=ft.Colors.YELLOW_200,
                                    ),
                                )
                            )
                            last_end = end
                        spans.append(ft.TextSpan(text[last_end:]))
                        return spans
                    except re.error as e:
                        return [
                            ft.TextSpan(
                                f"Invalid Regex: {e}\n\n",
                                style=ft.TextStyle(color=ft.Colors.RED),
                            ),
                            ft.TextSpan(text),
                        ]

                if language == "Pāḷi":
                    pali_text_spans = get_highlighted_spans(
                        pali_text_lower, search_term
                    )
                    eng_text_spans = [ft.TextSpan(eng_trans or "")]
                else:  # English
                    pali_text_spans = [ft.TextSpan(pali_text_lower)]
                    eng_text_spans = get_highlighted_spans(
                        eng_trans or "", search_term
                    )

                pali_text_widget = ft.Text(spans=pali_text_spans, selectable=True)
                pali_text_widget.data = pali_text_spans

                eng_text_widget = ft.Text(
                    spans=eng_text_spans, selectable=True, color=ft.Colors.GREY_700
                )
                eng_text_widget.data = eng_text_spans

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
                                pali_text_widget,
                                ft.Divider(height=5, color="transparent"),
                                eng_text_widget,
                            ]
                        ),
                    )
                )
                self.results_column.controls.append(result_card)

        self.page.update()

    def clear_clicked(self, e):
        self.search_term_field.value = ""
        self.results_search_field.value = ""
        self.results_column.controls.clear()
        self.results_container.visible = False  # Hide container on clear
        self.page.update()

    def handle_text_search(self, e: ft.ControlEvent):
        query = (e.data or "").lower()

        for control in self.results_column.controls:
            if not isinstance(control, ft.Card):
                continue

            card = control
            found_in_card = False

            card_content_column = card.content.content  # type: ignore
            pali_text_widget = card_content_column.controls[1]
            eng_text_widget = card_content_column.controls[3]

            # Pali text
            if hasattr(pali_text_widget, "data") and pali_text_widget.data:
                original_spans = pali_text_widget.data
                if query:
                    new_spans, found = self._create_highlighted_spans(
                        original_spans, query
                    )
                    pali_text_widget.spans = new_spans
                    if found:
                        found_in_card = True
                else:
                    pali_text_widget.spans = original_spans

            # English text
            if hasattr(eng_text_widget, "data") and eng_text_widget.data:
                original_spans = eng_text_widget.data

                if isinstance(original_spans, str):
                    original_spans = [
                        ft.TextSpan(
                            original_spans, style=ft.TextStyle(color=ft.Colors.GREY_700)
                        )
                    ]

                if query:
                    new_spans, found = self._create_highlighted_spans(
                        original_spans, query
                    )
                    eng_text_widget.spans = new_spans
                    if found:
                        found_in_card = True
                else:
                    eng_text_widget.spans = original_spans

                eng_text_widget.value = None

            if query and found_in_card:
                card.content.border = ft.border.all(2, HIGHLIGHT_COLOUR)  # type: ignore
                card.content.border_radius = 20  # type: ignore
            else:
                card.content.border = None  # type: ignore
                card.content.border_radius = None  # type: ignore

        self.page.update()

    def _create_highlighted_spans(
        self, spans: list[ft.TextSpan], query: str
    ) -> tuple[list[ft.TextSpan], bool]:
        new_spans = []
        found_match = False

        for span in spans:
            if not isinstance(span, ft.TextSpan) or not span.text:
                new_spans.append(span)
                continue

            text = span.text
            parts = re.split(f"({re.escape(query)})", text, flags=re.IGNORECASE)

            if len(parts) > 1:
                found_match = True
                for i, part in enumerate(parts):
                    if not part:
                        continue
                    if i % 2 == 1:  # the matched part
                        original_style = span.style if span.style else ft.TextStyle()

                        new_style = ft.TextStyle(
                            size=original_style.size,
                            weight=original_style.weight,
                            italic=original_style.italic,
                            font_family=original_style.font_family,
                            color=ft.Colors.BLACK,
                            bgcolor=HIGHLIGHT_COLOUR,
                            decoration=original_style.decoration,
                            decoration_color=original_style.decoration_color,
                            decoration_style=original_style.decoration_style,
                            height=original_style.height,
                        )
                        new_spans.append(ft.TextSpan(part, style=new_style))
                    else:  # the parts not matching
                        new_spans.append(ft.TextSpan(part, style=span.style))
            else:
                new_spans.append(span)

        return new_spans, found_match
