import re

import flet as ft

from gui2.toolkit import ToolKit
from tools.pali_text_files import cst_texts
from tools.tipitaka_db import search_all_cst_texts, search_book

# Style constants from pass1_auto_view.py
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=ft.Colors.GREY_500, size=10)
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
FILTER_HIGHLIGHT_COLOUR = ft.Colors.CYAN_200


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
            on_submit=self.handle_text_search,
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

            self.count_widget = ft.Text(count_message)
            self.original_count_text = count_message
            self.results_column.controls.append(self.count_widget)

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
                    eng_text_spans = get_highlighted_spans(eng_trans or "", search_term)

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
                result_card.pali_text_raw = pali_text_lower  # type: ignore
                result_card.eng_text_raw = eng_trans or ""  # type: ignore
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

        if not hasattr(self, "count_widget") or not self.results_column.controls:
            return

        total_cards = len(self.results_column.controls) - 1
        visible_count = 0

        for control in self.results_column.controls[1:]:
            if not isinstance(control, ft.Card):
                continue

            card = control

            if not query:
                card.visible = True
                card_content_column = card.content.content  # type: ignore
                pali_text_widget = card_content_column.controls[1]
                eng_text_widget = card_content_column.controls[3]

                if hasattr(pali_text_widget, "data"):
                    pali_text_widget.spans = pali_text_widget.data
                if hasattr(eng_text_widget, "data"):
                    eng_text_widget.spans = eng_text_widget.data
                    eng_text_widget.value = None
                visible_count += 1
                continue

            pali_raw = getattr(card, "pali_text_raw", "")  # type: ignore
            eng_raw = getattr(card, "eng_text_raw", "")  # type: ignore

            try:
                regex = re.compile(query, re.IGNORECASE)
                match_pali = bool(regex.search(pali_raw)) if pali_raw else False
                match_eng = bool(regex.search(eng_raw)) if eng_raw else False
            except re.error:
                match_pali = query in pali_raw.lower() if pali_raw else False
                match_eng = query in eng_raw.lower() if eng_raw else False

            found_in_card = match_pali or match_eng

            if found_in_card:
                card.visible = True
                visible_count += 1

                card_content_column = card.content.content  # type: ignore
                pali_text_widget = card_content_column.controls[1]
                eng_text_widget = card_content_column.controls[3]

                if hasattr(pali_text_widget, "data"):
                    pali_text_widget.spans = pali_text_widget.data
                if hasattr(eng_text_widget, "data"):
                    eng_text_widget.spans = eng_text_widget.data
                    eng_text_widget.value = None

                if match_pali and hasattr(pali_text_widget, "data"):
                    new_spans, _ = self._create_highlighted_spans(
                        pali_text_widget.data, query
                    )
                    pali_text_widget.spans = new_spans

                if match_eng and hasattr(eng_text_widget, "data"):
                    new_spans, _ = self._create_highlighted_spans(
                        eng_text_widget.data, query
                    )
                    eng_text_widget.spans = new_spans
            else:
                card.visible = False

        if query:
            self.count_widget.value = (
                f"Showing {visible_count} / {total_cards} results."
            )
        elif hasattr(self, "original_count_text"):
            self.count_widget.value = self.original_count_text

        self.results_search_field.focus()
        self.page.update()

    def _create_highlighted_spans(
        self, spans: list[ft.TextSpan], query: str
    ) -> tuple[list[ft.TextSpan], bool]:
        new_spans = []
        found_match = False

        regex = None
        try:
            regex = re.compile(query, re.IGNORECASE)
        except re.error:
            pass

        for span in spans:
            if not isinstance(span, ft.TextSpan) or not span.text:
                new_spans.append(span)
                continue

            text = span.text

            if regex:
                try:
                    matches = list(regex.finditer(text))
                    if matches:
                        found_match = True
                        last_end = 0
                        for match in matches:
                            start, end = match.span()
                            new_spans.append(ft.TextSpan(text[last_end:start]))
                            new_style = ft.TextStyle(
                                color=ft.Colors.BLACK,
                                bgcolor=FILTER_HIGHLIGHT_COLOUR,
                            )
                            new_spans.append(
                                ft.TextSpan(text[start:end], style=new_style)
                            )
                            last_end = end
                        new_spans.append(ft.TextSpan(text[last_end:]))
                        continue
                except re.error:
                    pass

            escaped = re.escape(query)
            parts = re.split(f"({escaped})", text, flags=re.IGNORECASE)

            if len(parts) > 1:
                found_match = True
                for i, part in enumerate(parts):
                    if not part:
                        continue
                    if i % 2 == 1:
                        new_style = ft.TextStyle(
                            color=ft.Colors.BLACK,
                            bgcolor=FILTER_HIGHLIGHT_COLOUR,
                        )
                        new_spans.append(ft.TextSpan(part, style=new_style))
                    else:
                        new_spans.append(ft.TextSpan(part))
            else:
                new_spans.append(span)

        return new_spans, found_match
