from json import dump, load
from pathlib import Path

import flet as ft
import pyperclip
from rich import print

from db.models import DpdHeadword
from gui2.dpd_fields_functions import make_dpd_headword_from_dict
from gui2.books import sutta_central_books
from gui2.daily_log import DailyLog
from gui2.database_manager import DatabaseManager
from gui2.mixins import SandhiOK, SnackBarMixin
from gui2.paths import Gui2Paths
from gui2.spelling import SpellingMistakesFileManager
from gui2.variants import VariantReadingFileManager
from tools.fast_api_utils import request_dpd_server
from tools.goldendict_tools import open_in_goldendict_os

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass1AddController(SandhiOK, SnackBarMixin):
    from gui2.pass1_add_view import Pass1AddView

    def __init__(
        self, ui: Pass1AddView, db: DatabaseManager, daily_log: DailyLog
    ) -> None:
        self.ui = ui
        self.db = db
        self.daily_log = daily_log

        self.pass1_books = sutta_central_books
        self.pass1_books_list = [k for k in self.pass1_books]
        self.book_to_process: str

        self.auto_processed_filepath: Path
        self.auto_processed_dict: dict[str, dict[str, str]]
        self.auto_processed_iter = iter([])

        self.word_in_text: str
        self.sentence_data: dict[str, str]

        self.variants = VariantReadingFileManager()
        self.spelling_mistakes = SpellingMistakesFileManager()

    def process_book(self, book: str):
        self.book_to_process = book
        self.load_json()
        is_next_item = self.get_next_item()
        if is_next_item:
            self.load_into_gui()
        else:
            self.ui.clear_all_fields()

    def load_json(self):
        self.gui2pth = Gui2Paths()
        self.auto_processed_filepath = (
            self.gui2pth.gui2_data_path / f"pass1_auto_{self.book_to_process}.json"
        )
        try:
            self.auto_processed_dict = load(
                self.auto_processed_filepath.open("r", encoding="utf-8")
            )
            # dict will change size, so work on a copy
            self.auto_processed_dict_copy = self.auto_processed_dict.copy()
            self.auto_processed_iter = iter(self.auto_processed_dict_copy.items())
            self.ui.update_remaining(f"{len(self.auto_processed_dict)}")
        except FileNotFoundError:
            self.ui.update_message("file not found.")

    def get_next_item(self):
        try:
            self.word_in_text, self.sentence_data = next(self.auto_processed_iter)
            self.ui.update_remaining(f"{len(self.auto_processed_dict)}")
            print(self.word_in_text)
            print(self.sentence_data)
            return True
        except StopIteration:
            self.ui.clear_all_fields()
            self.ui.update_message("No more words to process.")
            self.ui.update_remaining(f"{len(self.auto_processed_dict)}")
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

    def make_dpd_headword_and_add_to_db(self):
        # Collect data from UI fields into a dictionary
        field_data: dict[str, str] = {
            field_name: field.value
            for field_name, field in self.ui.dpd_fields.fields.items()
            if hasattr(DpdHeadword, field_name)  # Only include relevant fields
        }

        # Create the DpdHeadword object using the imported function
        new_word = make_dpd_headword_from_dict(field_data)

        # Set fields not derived directly from the input dict
        new_word.id = self.db.get_next_id()
        new_word.origin = "pass1"

        committed, message = self.db.add_word_to_db(new_word)
        if committed:
            # open in browser
            request_dpd_server(new_word.id)

            # update the log (this now automatically updates the appbar)
            self.daily_log.increment("pass1")

            self.remove_word_and_save_json()
            self.ui.clear_all_fields()

            self.db.get_all_lemma_1_and_lemma_clean()
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
            del self.auto_processed_dict[self.word_in_text]
            dump(
                self.auto_processed_dict,
                self.auto_processed_filepath.open("w"),
                ensure_ascii=False,
                indent=2,
            )
            self.ui.update_message(f"{self.word_in_text} deleted")
        except KeyError as e:
            self.ui.clear_all_fields()
            self.ui.update_message(f"{e}")
