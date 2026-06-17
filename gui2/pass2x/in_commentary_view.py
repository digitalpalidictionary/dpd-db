"""Pass2x tab — "in commentary" GUI (stage 2).

The Pass2x tab sits between Pass2Pre and Pass2Auto and hosts a growing set of
buttons for finding words that still need an example. The first button is
**"in commentary"**: it walks the user through commentary words that are
inflections of incomplete headwords, offering Yes / No / Pass on a selectable
list of example sentences. A "yes" is persisted in the ``matched`` shape that
Pass2Auto consumes.
"""

import flet as ft

from gui2.flet_functions import highlight_terms
from gui2.pass2_pre_new_word_manager import Pass2NewWordManager
from gui2.pass2x.in_commentary_tui import Example
from gui2.toolkit import ToolKit
from tools.cst_source import CstSourceSuttaExample

LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
SEARCH_COLOUR = ft.Colors.AMBER
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=LABEL_COLOUR, size=10)


class Pass2xInCommentaryView(ft.Column):
    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        from gui2.pass2x.in_commentary_controller import Pass2xInCommentaryController

        super().__init__(expand=True, controls=[], spacing=0)
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit
        self.controller = Pass2xInCommentaryController(self, toolkit)
        self.pass2_new_word_manager: Pass2NewWordManager = (
            toolkit.pass2_new_word_manager
        )
        self.selected_sentence_index: int = 0
        self.examples_list: list[Example] = []
        self.filtered_translations: list[tuple[int, Example]] = []
        self.search_query: str = ""
        self.examples_page_size: int = 50
        self.examples_shown: int = 50

        self.search_bar = ft.SearchBar(
            bar_hint_text="filter examples",
            on_change=self.handle_search,
            width=300,
        )
        self.preprocessed_count_field = ft.TextField(
            "",
            label="Counter",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=400,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            expand=True,
            read_only=True,
        )
        self.word_in_text_field = ft.TextField(
            "",
            expand=True,
            label="Word in text (edit + Enter to re-search)",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_word_in_text_submit,
        )
        self.headword_lemma_1_field = ft.TextField(
            "",
            width=500,
            label="Headword",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            expand=True,
        )
        self.headword_pos_field = ft.TextField(
            "",
            width=120,
            label="POS",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
        )
        self.headword_meaning_field = ft.TextField(
            "",
            expand=True,
            label="Meaning",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
        )
        self.exceptions_field = ft.TextField(
            "",
            on_submit=self.handle_add_exception,
            border_radius=20,
            width=300,
            expand=True,
            label="add word to exceptions (blank = current word)",
            label_style=TEXT_FIELD_LABEL_STYLE,
        )
        self.message_field = ft.TextField(
            "",
            expand=True,
            color=ft.Colors.BLUE_200,
            border_radius=20,
            read_only=True,
        )
        self.examples_count_field = ft.TextField(
            "",
            width=60,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            read_only=True,
            text_align=ft.TextAlign.RIGHT,
        )

        top_fixed_section_controls = [
            ft.Row(
                controls=[
                    ft.ElevatedButton(
                        "in commentary",
                        on_click=self.handle_in_commentary_click,
                    ),
                    self.preprocessed_count_field,
                    self.search_bar,
                ],
            ),
            ft.Row(controls=[self.word_in_text_field], spacing=10),
            ft.Row(controls=[self.headword_lemma_1_field], spacing=10),
            ft.Row(
                controls=[self.headword_pos_field, self.headword_meaning_field],
                spacing=10,
            ),
            ft.Divider(),
            ft.Row(
                controls=[
                    ft.ElevatedButton("Yes", on_click=self.handle_yes_click),
                    ft.ElevatedButton("No", on_click=self.handle_no_click),
                    ft.ElevatedButton("New", on_click=self.handle_new_click),
                    ft.ElevatedButton("Pass", on_click=self.handle_pass_click),
                    self.exceptions_field,
                ],
            ),
            ft.Row(
                controls=[self.message_field, self.examples_count_field],
                spacing=5,
            ),
        ]

        self.top_fixed_section = ft.Container(
            ft.Column(controls=top_fixed_section_controls, expand=False, spacing=5),
            padding=ft.Padding(0, 10, 0, 0),
        )
        self.examples_field = ft.Container(content=None, expand=True)
        self.examples_scrollable_section = ft.Column(
            controls=[self.examples_field],
            expand=True,
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
        )

        self.controls = [
            self.top_fixed_section,
            ft.Divider(),
            self.examples_scrollable_section,
        ]

    # --- ui updates ---

    def update_message(self, message: str) -> None:
        self.message_field.value = message
        self.page.update()

    def update_examples(self, examples_group: ft.RadioGroup | None) -> None:
        self.examples_field.content = examples_group
        self.page.update()

    def update_word_in_text(self, word: str) -> None:
        self.word_in_text_field.value = word
        self.page.update()

    def update_preprocessed_count(self, count: str) -> None:
        self.preprocessed_count_field.value = str(count)
        self.page.update()

    def update_examples_count(self, count: int) -> None:
        self.examples_count_field.value = str(count)
        self.page.update()

    # --- example list ---

    def make_examples_list(self, examples: list[Example]) -> ft.RadioGroup:
        self.examples_list = examples
        self.search_query = ""
        self.search_bar.value = ""
        self.examples_shown = self.examples_page_size
        self._filter()
        self._reset_selection()
        self.update_examples_count(len(self.filtered_translations))
        return self._build_radio_group()

    def _filter(self) -> None:
        """Build the list of selectable (translation) examples matching the query.

        Commentary examples are excluded here — they are always shown, copyable
        but not selectable, regardless of the filter.
        """
        self.filtered_translations = []
        for index, example in enumerate(self.examples_list):
            if example.is_commentary:
                continue
            if self.search_query:
                text = f"{example.pali_raw} {example.english}".lower()
                if self.search_query not in text:
                    continue
            self.filtered_translations.append((index, example))

    def _reset_selection(self) -> None:
        self.selected_sentence_index = (
            self.filtered_translations[0][0] if self.filtered_translations else -1
        )

    def _example_block(self, example: Example, radio_value: str | None) -> ft.Column:
        """One example row. ``radio_value=None`` renders it unselectable."""
        sentence = example.pali_raw.lower().replace("ṁ", "ṃ")
        header_controls: list[ft.Control] = []
        if radio_value is not None:
            header_controls.append(ft.Radio(value=radio_value))
        header_controls.append(
            ft.Text(example.source, selectable=True, color=HIGHLIGHT_COLOUR)
        )
        if example.book_name:
            header_controls.append(ft.Text(example.book_name, selectable=True))
        header_controls.append(
            ft.Text(example.paranum, selectable=True, color=LABEL_COLOUR)
        )
        return ft.Column(
            controls=[
                ft.Row(
                    controls=header_controls,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(
                    content=ft.SelectionArea(
                        content=ft.Text(
                            spans=highlight_terms(
                                sentence,
                                [
                                    (self.controller.word_in_text, HIGHLIGHT_COLOUR),
                                    (self.search_query, SEARCH_COLOUR),
                                ],
                            ),
                            expand=True,
                        )
                    ),
                    padding=ft.padding.only(left=10),
                ),
                ft.Container(
                    content=ft.SelectionArea(
                        content=ft.Text(
                            spans=highlight_terms(
                                example.english,
                                [(self.search_query, SEARCH_COLOUR)],
                            ),
                            expand=True,
                            color=ft.Colors.GREY_500,
                        )
                    ),
                    padding=ft.padding.only(left=10),
                ),
                ft.Divider(),
            ],
            spacing=4,
            expand=True,
        )

    def _build_radio_group(self) -> ft.RadioGroup:
        example_controls: list[ft.Control] = []
        # commentary (#0) — always shown, never selectable
        # commentary examples — always shown, never selectable (no radio)
        for example in self.examples_list:
            if example.is_commentary:
                example_controls.append(self._example_block(example, None))

        visible = self.filtered_translations[: self.examples_shown]
        for index, example in visible:
            example_controls.append(self._example_block(example, str(index)))

        total = len(self.filtered_translations)
        buttons: list[ft.Control] = []
        if self.examples_shown < total:
            buttons.append(
                ft.TextButton(
                    f"More ({total - self.examples_shown} remaining)",
                    on_click=self._handle_more_click,
                )
            )
        if self.examples_shown > self.examples_page_size:
            buttons.append(ft.TextButton("Less", on_click=self._handle_less_click))
        if buttons:
            example_controls.append(ft.Row(controls=buttons))

        return ft.RadioGroup(
            content=ft.Column(
                controls=example_controls,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            on_change=self.handle_example_selection_change,
        )

    def handle_search(self, e: ft.ControlEvent) -> None:
        self.search_query = str(e.data or "").lower()
        if not self.examples_list:
            return
        self.examples_shown = self.examples_page_size
        self._filter()
        self._reset_selection()
        self.update_examples_count(len(self.filtered_translations))
        self.update_examples(self._build_radio_group())

    def _handle_more_click(self, e: ft.ControlEvent) -> None:
        self.examples_shown += self.examples_page_size
        self.update_examples(self._build_radio_group())

    def _handle_less_click(self, e: ft.ControlEvent) -> None:
        self.examples_shown = self.examples_page_size
        self.update_examples(self._build_radio_group())

    def handle_example_selection_change(self, e: ft.ControlEvent) -> None:
        if e.control.value is not None:
            self.selected_sentence_index = int(e.control.value)

    # --- button handlers ---

    def handle_in_commentary_click(self, e: ft.ControlEvent) -> None:
        self.update_message("loading...")
        self.controller.load_in_commentary()
        self.controller.load_next_word()

    def handle_word_in_text_submit(self, e: ft.ControlEvent) -> None:
        word = (self.word_in_text_field.value or "").strip()
        if not word:
            return
        self.update_message("searching examples...")
        self.controller.search_word(word)

    def _selected_example(self) -> Example | None:
        if 0 <= self.selected_sentence_index < len(self.examples_list):
            return self.examples_list[self.selected_sentence_index]
        return None

    def _current_headword_id(self) -> int | None:
        controller = self.controller
        if 0 <= controller.headword_index < len(controller.headwords):
            return controller.headwords[controller.headword_index].id
        return None

    def handle_yes_click(self, e: ft.ControlEvent) -> None:
        example = self._selected_example()
        headword_id = self._current_headword_id()
        if example is None or headword_id is None:
            return
        sentence = CstSourceSuttaExample(
            example.source, example.paranum, example.pali_raw
        )
        message = self.controller.file_manager.update_matched(
            self.controller.word_in_text, headword_id, sentence
        )
        self.update_message(message)
        self.controller.load_next_headword()

    def handle_no_click(self, e: ft.ControlEvent) -> None:
        headword_id = self._current_headword_id()
        if headword_id is None:
            return
        message = self.controller.file_manager.update_unmatched(
            self.controller.word_in_text, headword_id
        )
        self.update_message(message)
        self.controller.load_next_headword()

    def handle_new_click(self, e: ft.ControlEvent) -> None:
        example = self._selected_example()
        if example is None:
            return
        sentence = CstSourceSuttaExample(
            example.source, example.paranum, example.pali_raw
        )

        def on_ok(e: ft.ControlEvent) -> None:
            self.new_word_dialog.open = False
            self.page.update()
            comment_val = comment_input.value or ""
            message = self.pass2_new_word_manager.update_new_word(
                self.controller.word_in_text,
                sentence,
                comment=comment_val,
            )
            self.selected_sentence_index = 0
            self.update_message(message)

        comment_input = ft.TextField(expand=True, autofocus=True, on_submit=on_ok)

        self.new_word_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.Text(
                                "Whats the meaning of the new word?",
                                size=14,
                                color=ft.Colors.GREY_500,
                            )
                        ]
                    ),
                    ft.Row([comment_input]),
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("OK", on_click=on_ok),
            ],
        )

        self.page.open(self.new_word_dialog)
        self.page.update()

    def handle_pass_click(self, e: ft.ControlEvent) -> None:
        self.controller.load_next_headword()

    def handle_add_exception(self, e: ft.ControlEvent) -> None:
        word = (
            self.exceptions_field.value or ""
        ).strip() or self.controller.word_in_text
        if not word:
            return
        self.controller.exceptions.add(word)
        self.exceptions_field.value = ""
        self.update_message(f"{word} added to exceptions.")
        self.controller.skip_word(word)

    def clear_all_fields(self) -> None:
        self.message_field.value = ""
        self.preprocessed_count_field.value = ""
        self.word_in_text_field.value = ""
        self.headword_lemma_1_field.value = ""
        self.headword_pos_field.value = ""
        self.headword_meaning_field.value = ""
        self.exceptions_field.value = ""
        self.examples_field.content = None
        self.examples_count_field.value = ""
        self.search_bar.value = ""
        self.search_query = ""
        self.examples_list = []
        self.filtered_translations = []
        self.selected_sentence_index = -1
        self.page.update()
