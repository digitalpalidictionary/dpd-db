from json import dump, load
from pathlib import Path
import flet as ft
import pyperclip
from db.models import DpdHeadword
from gui2.class_daily_log import DailyLog
from gui2.class_database import DatabaseManager
from gui2.class_mixins import SandhiOK, SnackBarMixin

from gui2.class_books import pass1_books
from tools.goldendict_tools import open_in_goldendict_os
from rich import print

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass1Controller(SandhiOK, SnackBarMixin):
    from gui2.tab_pass1_view import Pass1View

    def __init__(self, ui: Pass1View, db: DatabaseManager) -> None:
        self.ui = ui
        self.db = db

        self.daily_log = DailyLog()

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
        is_next_item = self.get_next_item()
        if is_next_item:
            self.load_into_gui()
        else:
            self.ui.clear_all_fields()

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
            self.ui.clear_all_fields()
            self.ui.update_message("No more words to process.")
            return False

    def load_into_gui(self):
        open_in_goldendict_os(self.word_in_text)
        pyperclip.copy(self.word_in_text)
        self.ui.word_in_text.value = self.word_in_text
        self.ui.word_in_text.update()

        for field, data in self.sentence_data.items():
            if field in self.ui.dpd_fields.fields:
                self.ui.dpd_fields.fields[field].value = data

        self.ui.page.update()

    def make_dpdheadword_and_add_to_db(self):
        new_word = DpdHeadword()
        for field_name, field in self.ui.dpd_fields.fields.items():
            if hasattr(new_word, field_name):
                setattr(new_word, field_name, field.value)

        new_word.id = self.db.get_next_id()
        new_word.origin = "pass1"

        committed, message = self.db.add_word_to_db(new_word)
        if committed:
            mesage = self.daily_log.increment("pass1")
            self.show_snackbar(self.ui.page, mesage)
            self.remove_word_and_save_json()
            self.ui.clear_all_fields()

            self.db.get_all_lemma_1()
            is_next_item = self.get_next_item()
            if is_next_item:
                self.load_into_gui()
                self.ui.update_message(
                    f"{self.ui.dpd_fields.fields['lemma_1'].value} added to db"
                )
            else:
                self.ui.clear_all_fields()
        else:
            self.ui.update_message(
                f"""commit failed for {self.ui.dpd_fields.fields["lemma_1"].value}\n{message}"""
            )

    def remove_word_and_save_json(self):
        try:
            del self.preprocessed_dict[self.word_in_text]
            dump(
                self.preprocessed_dict,
                self.preprocessed_filepath.open("w"),
                ensure_ascii=False,
                indent=2,
            )
            self.ui.update_message(f"{self.word_in_text} deleted")
        except KeyError as e:
            self.ui.clear_all_fields()
            self.ui.update_message(f"{e}")
