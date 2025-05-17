import flet as ft

from gui2.toolkit import ToolKit
from gui2.books import SuttaCentralSegment
from gui2.flet_functions import highlight_word_in_sentence
from tools.cst_source_sutta_example import CstSourceSuttaExample


class Pass2PreProcessView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        from gui2.pass2_pre_controller import Pass2PreController

        super().__init__(
            expand=True,
            controls=[],
            spacing=0,
        )
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit
        self.controller = Pass2PreController(
            self,
            toolkit,
        )
        self.selected_sentence_index: int = 0

        # Define constants
        LABEL_WIDTH: int = 150
        COLUMN_WIDTH: int = 700

        # Define controls
        self.message_field = ft.Text(
            "",
            expand=True,
            color=ft.Colors.BLUE_200,
            selectable=True,
        )
        self.book_options = [
            ft.dropdown.Option(key=item, text=item)
            for item in self.controller.sutta_central_books_list
        ]
        self.books_dropdown = ft.Dropdown(
            options=self.book_options,
            width=200,
            text_size=14,
            border_color=ft.Colors.BLUE_200,
        )
        self.preprocessed_count_field = ft.Text(
            "",
            expand=True,
        )
        self.search_bar = ft.SearchBar(
            bar_hint_text="",
            on_change=self.handle_search,
            width=300,
            autofocus=True,
        )
        self.word_in_text_field = ft.Text(
            "",
            width=COLUMN_WIDTH,
            expand=True,
            color=ft.Colors.BLUE_200,
            selectable=True,
            size=14,
        )
        self.headword_lemma_1_field = ft.Text(
            "",
            width=500,
            selectable=True,
            size=14,
        )
        self.headword_pos_field = ft.Text(
            "",
            width=120,
            selectable=True,
            size=14,
        )
        self.headword_meaning_field = ft.Text(
            "",
            width=COLUMN_WIDTH,
            expand=True,
            selectable=True,
            size=14,
        )
        self.examples_field = ft.Container(
            content=None,
            width=COLUMN_WIDTH,
            expand=True,
        )

        top_fixed_section_controls = [
            ft.Row(
                controls=[
                    ft.Text("", width=LABEL_WIDTH),
                    self.message_field,
                ],
            ),
            ft.Row(
                controls=[
                    ft.Text("book", width=LABEL_WIDTH, color=ft.Colors.GREY_500),
                    self.books_dropdown,
                    ft.ElevatedButton(
                        "PreProcess Book",
                        on_click=self.handle_book_click,
                    ),
                    self.preprocessed_count_field,
                    self.search_bar,
                ],
            ),
            ft.Row(
                controls=[
                    ft.Text(
                        "word in text",
                        width=LABEL_WIDTH,
                        color=ft.Colors.GREY_500,
                    ),
                    self.word_in_text_field,
                ],
                spacing=10,
            ),
            ft.Row(
                controls=[
                    ft.Text(
                        "headword",
                        width=LABEL_WIDTH,
                        color=ft.Colors.GREY_500,
                    ),
                    self.headword_lemma_1_field,
                ],
                spacing=10,
            ),
            ft.Row(
                controls=[
                    ft.Text(
                        "meaning",
                        width=LABEL_WIDTH,
                        color=ft.Colors.GREY_500,
                    ),
                    self.headword_pos_field,
                    self.headword_meaning_field,
                ],
                spacing=10,
            ),
            ft.Divider(),
            ft.Row(
                controls=[
                    ft.Text(
                        "",
                        width=LABEL_WIDTH,
                        color=ft.Colors.GREY_500,
                    ),
                    ft.ElevatedButton(
                        "Yes",
                        width=LABEL_WIDTH,
                        on_click=self.handle_yes_click,
                    ),
                    ft.ElevatedButton(
                        "No",
                        width=LABEL_WIDTH,
                        on_click=self.handle_no_click,
                    ),
                    ft.ElevatedButton(
                        "New",
                        width=LABEL_WIDTH,
                        on_click=self.handle_new_click,
                    ),
                    ft.ElevatedButton(
                        "Pass",
                        width=LABEL_WIDTH,
                        on_click=self.handle_pass_click,
                    ),
                ],
            ),
        ]

        self.top_fixed_section = ft.Column(
            controls=top_fixed_section_controls, expand=False, spacing=5
        )

        self.examples_content_row = ft.Row(
            controls=[
                ft.Text(
                    "examples",
                    width=LABEL_WIDTH,
                    color=ft.Colors.GREY_500,
                ),
                self.examples_field,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        self.examples_scrollable_section = ft.Column(
            controls=[self.examples_content_row],
            expand=True,
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
        )

        self.controls = [
            self.top_fixed_section,
            ft.Divider(),
            self.examples_scrollable_section,
        ]

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def update_examples(self, examples_group: ft.RadioGroup | None):
        self.examples_field.content = examples_group
        self.page.update()

    def update_word_in_text(self, word: str):
        self.word_in_text_field.value = word
        self.page.update()

    def update_preprocessed_count(self, count: str):
        self.preprocessed_count_field.value = str(count)
        self.page.update()

    def handle_book_click(self, e):
        if self.books_dropdown.value:
            self.update_message("loading...")
            # Ensure data is loaded before processing
            self.controller._load_data()
            self.controller.find_words_with_missing_examples(
                self.books_dropdown.value,
                self.toolkit.paths,
            )
            self.controller.load_next_word()

    def handle_yes_click(self, e):
        headword_id = self.controller.headwords[self.controller.headword_index].id
        sentence: SuttaCentralSegment | CstSourceSuttaExample | None = None

        if sentences := self.controller.missing_examples_dict.get(
            self.controller.word_in_text, []
        ):
            if self.selected_sentence_index < len(sentences):
                sentence = sentences[self.selected_sentence_index]

        if sentence is None:
            return

        message = self.controller.file_manager.update_matched(
            self.controller.word_in_text, headword_id, sentence
        )
        self.update_message(message)

        # Update log (this now automatically updates the appbar)
        self.controller.daily_log.increment("pass2_pre")

        self.selected_sentence_index = 0

        self.controller.load_next_headword()

    def handle_no_click(self, e):
        message = self.controller.file_manager.update_unmatched(
            self.controller.word_in_text,
            self.controller.headwords[self.controller.headword_index].id,
        )
        self.update_message(message)
        # Update log (this now automatically updates the appbar)
        self.controller.daily_log.increment("pass2_pre")
        self.selected_sentence_index = 0
        self.controller.load_next_headword()

    def handle_pass_click(self, e):
        self.selected_sentence_index = 0
        self.controller.load_next_headword()

    def handle_new_click(self, e):
        sentence: SuttaCentralSegment | CstSourceSuttaExample | None = None
        if sentences := self.controller.missing_examples_dict.get(
            self.controller.word_in_text, []
        ):
            if self.selected_sentence_index < len(sentences):
                sentence = sentences[self.selected_sentence_index]

        if sentence is None:
            return

        message = self.controller.file_manager.update_new_word(
            self.controller.word_in_text, sentence
        )
        self.selected_sentence_index = 0
        self.update_message(message)
        self.controller.daily_log.increment("pass2_pre")

    def make_examples_list(
        self, examples_list: list[SuttaCentralSegment] | list[CstSourceSuttaExample]
    ) -> ft.RadioGroup:
        example_controls: list[ft.Control] = []
        for counter, example in enumerate(examples_list):
            if isinstance(example, SuttaCentralSegment):
                source = example.segment
                sutta = ""
                pali = example.pali
                english = example.english
            elif isinstance(example, CstSourceSuttaExample):
                source = example.source
                sutta = example.sutta
                pali = example.example
                english = ""

            example_controls.append(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Radio(value=str(counter)),
                                ft.Text(
                                    source,
                                    selectable=True,
                                ),
                                ft.Text(
                                    sutta,
                                    selectable=True,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Container(
                            content=ft.Text(
                                spans=highlight_word_in_sentence(
                                    self.controller.word_in_text,
                                    pali.lower().replace("ṁ", "ṃ"),
                                ),
                                expand=True,
                                selectable=True,
                            ),
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Container(
                            content=ft.Text(
                                english,
                                expand=True,
                                color=ft.Colors.GREY_500,
                                selectable=True,
                            ),
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Divider(),
                    ],
                    spacing=4,
                    expand=True,
                )
            )

        radio_group = ft.RadioGroup(
            content=ft.Column(
                controls=example_controls,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            on_change=self.handle_example_selection_change,
        )
        return radio_group

    def handle_example_selection_change(self, e: ft.ControlEvent):
        selected_example_index_str: str | None = e.control.value
        if selected_example_index_str is not None:
            self.selected_sentence_index = int(selected_example_index_str)

        print(
            f"Selected index stored: {self.selected_sentence_index}"
        )  # Optional: for debugging

    def handle_search(self, e: ft.ControlEvent) -> None:
        query = str(e.data or "").lower()
        if not self.examples_field.content or not query:
            return

        radio_group = self.examples_field.content

        for example_column in radio_group.content.controls:  # type: ignore
            if not isinstance(example_column, ft.Column):
                continue

            for control in example_column.controls:
                if isinstance(control, ft.Row):
                    for row_control in control.controls:
                        if isinstance(row_control, ft.Text):
                            self._simple_highlight(row_control, query)
                elif isinstance(control, ft.Container):
                    if isinstance(control.content, ft.Text):
                        self._simple_highlight(control.content, query)

        self.page.update()

    def _simple_highlight(self, text_control: ft.Text, query: str) -> None:
        if not query:
            text_control.color = None
            return

        text = str(text_control.value or "").lower()
        text_control.color = ft.Colors.AMBER if query in text else None
