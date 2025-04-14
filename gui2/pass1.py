from json import dump, load
from pathlib import Path
import flet as ft
from db.models import DpdHeadword
from gui2.database import DatabaseManager
from gui2.mixins import PopUpMixin, SandhiOK
from gui2.pass1_preprocess import pass1_books
from tools.goldendict_tools import open_in_goldendict_os


class Pass1View(ft.Column, PopUpMixin):
    def __init__(self, page: ft.Page) -> None:
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )
        PopUpMixin.__init__(self)
        self.page: ft.Page = page
        self.controller = Pass1Controller(self)
        self.pass1_fields = {}

        LABEL_WIDTH = 250
        BUTTON_WIDTH = 250

        # controls
        self.message_field = ft.Text("", color=ft.Colors.BLUE_200)
        self.book_options = [
            ft.dropdown.Option(key=item, text=item)
            for item in self.controller.pass1_books_list
        ]
        self.books_dropdown = ft.Dropdown(
            autofocus=True,
            options=self.book_options,
            width=300,
            text_size=14,
            border_color=ft.Colors.BLUE_200,
        )

        self.word_in_text = ft.TextField(
            "", width=LABEL_WIDTH, color=ft.Colors.BLUE_200, expand=True
        )
        self.pass1_fields["word_in_text"] = self.word_in_text

        self.controls.extend(
            [
                ft.Row(
                    controls=[
                        ft.Text("", width=LABEL_WIDTH),
                        self.message_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("book", width=LABEL_WIDTH),
                        self.books_dropdown,
                        ft.ElevatedButton(
                            "Process Book",
                            width=BUTTON_WIDTH,
                            on_click=self.handle_process_book_click,
                        ),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("word_in_text", width=LABEL_WIDTH),
                        self.word_in_text,
                    ],
                ),
            ]
        )

        field_names = [
            "lemma_1",
            "lemma_2",
            "pos",
            "grammar",
            "meaning_2",
            "root_key",
            "root_sign",
            "root_base",
            "family_root",
            "family_compound",
            "construction",
            "example_1",
            "translation_1",
            "example_2",
            "translation_2",
            "stem",
            "pattern",
            "comments",
        ]

        for name in field_names:
            label_text = ft.Text(value=name, width=LABEL_WIDTH)

            text_field = ft.TextField(width=700, expand=True, multiline=True)
            self.pass1_fields[name] = text_field

            row = ft.Row(
                controls=[label_text, text_field],
                alignment=ft.MainAxisAlignment.START,
            )

            self.controls.append(row)

        self.controls.append(
            ft.Row(
                [
                    ft.Text("", width=LABEL_WIDTH),
                    ft.ElevatedButton(
                        "Add to DB",
                        on_click=self.handle_add_to_db_click,
                        width=BUTTON_WIDTH,
                    ),
                    ft.ElevatedButton(
                        "Add to Sandhi",
                        on_click=self.handle_sandhi_ok_click,
                        width=BUTTON_WIDTH,
                    ),
                    ft.ElevatedButton(
                        "Pass",
                        on_click=self.handle_pass_click,
                        width=BUTTON_WIDTH,
                    ),
                    ft.ElevatedButton(
                        "Delete",
                        on_click=self.handle_delete_click,
                        width=BUTTON_WIDTH,
                    ),
                ]
            )
        )

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def handle_process_book_click(self, e):
        if self.books_dropdown.value:
            self.controller.process_book(self.books_dropdown.value)

    def handle_add_to_db_click(self, e):
        self.controller.make_dpdheadword_and_add_to_db()

    def handle_sandhi_ok_click(self, e):
        current_word = self.word_in_text.value
        if not current_word:
            self.update_message("No word selected.")
            return

        self.show_popup(
            page=self.page,
            prompt_message="Enter construction':",
            initial_value=self.word_in_text.value,
            on_submit=self.process_sandhi_popup_result,
        )

    def handle_pass_click(self, e):
        self.clear_all_fields()
        self.controller.get_next_item()
        self.controller.load_into_gui()

    def handle_delete_click(self, e):
        if self.word_in_text.value:
            del self.controller.preprocessed_dict[self.word_in_text.value]
            self.clear_all_fields()
            self.controller.get_next_item()
            self.controller.load_into_gui()
        else:
            self.update_message("No word_in_text.")

    def clear_all_fields(self):
        for field in self.pass1_fields.values():
            field.value = ""
            field.update()
        self.page.update()

    def process_sandhi_popup_result(self, breakup_value):
        """Handles the result after the sandhi popup closes."""

        if breakup_value is not None and self.word_in_text.value:
            self.controller.update_sandhi_ok(self.word_in_text.value, breakup_value)
            self.update_message(f"Sandhi added for {self.word_in_text.value}")
            self.controller.remove_word_and_save_json()
            self.clear_all_fields()
            self.controller.get_next_item()
            self.controller.load_into_gui()
        else:
            self.update_message("Sandhi input cancelled.")


class Pass1Controller(SandhiOK):
    def __init__(self, ui: Pass1View) -> None:
        self.ui: Pass1View = ui
        self.db = DatabaseManager()

        self.pass1_books = pass1_books
        self.pass1_books_list = [k for k in self.pass1_books]
        self.book_to_process: str

        self.preprocessed_filepath: Path
        self.preprocessed_dict: dict[str, dict[str, str]]
        self.preprocessed_iter = iter([])

        self.word_in_text: str
        self.sentence_data: dict[str, str]

    def process_book(self, book: str):
        self.book_to_process = book
        self.load_json()
        self.get_next_item()
        self.load_into_gui()

    def load_json(self):
        self.preprocessed_filepath = Path(
            f"gui2/data/{self.book_to_process}_preprocessed.json"
        )
        try:
            self.preprocessed_dict = load(
                self.preprocessed_filepath.open("r", encoding="utf-8")
            )
            # dict will change size, so work on a zopy
            self.preprocessed_dict_copy = self.preprocessed_dict.copy()
            self.preprocessed_iter = iter(self.preprocessed_dict_copy.items())
        except FileNotFoundError:
            self.ui.update_message("file not found.")

    def get_next_item(self):
        try:
            self.word_in_text, self.sentence_data = next(self.preprocessed_iter)
            print(self.word_in_text)
            print(self.sentence_data)
            return True
        except StopIteration:
            print("end of iter")
            return False

    def load_into_gui(self):
        open_in_goldendict_os(self.word_in_text)
        self.ui.pass1_fields["word_in_text"].value = self.word_in_text
        self.ui.pass1_fields["word_in_text"].update()

        for field, data in self.sentence_data.items():
            self.ui.pass1_fields[field].value = data
            self.ui.pass1_fields[field].update()

        # add lemma_2 to request and delete this
        self.ui.pass1_fields["lemma_2"].value = self.ui.pass1_fields["lemma_1"].value
        self.ui.pass1_fields[field].update()

        self.ui.page.update()

    def make_dpdheadword_and_add_to_db(self):
        new_word = DpdHeadword()
        for field, value in self.ui.pass1_fields.items():
            if hasattr(new_word, field):
                setattr(new_word, field, value.value)
        committed = self.db.add_word_to_db(new_word)
        if committed:
            self.ui.update_message(
                f"{self.ui.pass1_fields['lemma_1'].value} added to db"
            )
            self.remove_word_and_save_json()
            self.ui.clear_all_fields()
            self.get_next_item()
            self.load_into_gui()
        else:
            self.ui.update_message(
                f"commit failed for{self.ui.pass1_fields['lemma_1'].value}"
            )

    def remove_word_and_save_json(self):
        del self.preprocessed_dict[self.word_in_text]
        dump(
            self.preprocessed_dict,
            self.preprocessed_filepath.open("w"),
            ensure_ascii=False,
            indent=2,
        )
