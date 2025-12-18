# -*- coding: utf-8 -*-

import flet as ft
import pyperclip
from rich import print

from db.models import DpdHeadword
from gui2.additions_manager import AdditionsManager
from gui2.books import sutta_central_books
from gui2.daily_log import DailyLog
from gui2.database_manager import DatabaseManager
from gui2.dpd_fields_functions import make_dpd_headword_from_dict
from gui2.mixins import SandhiOK, SnackBarMixin
from gui2.pass1_add_view import Pass1AddView
from gui2.pass1_auto_controller import Pass1AutoController
from gui2.paths import Gui2Paths
from gui2.spelling import SpellingMistakesFileManager
from gui2.toolkit import ToolKit
from gui2.user import UsernameManager
from gui2.variants import VariantReadingFileManager
from tools.fast_api_utils import request_dpd_server
from tools.goldendict_tools import open_in_goldendict_os
from tools.wordfinder_manager import WordFinderManager

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass1AddController(SandhiOK, SnackBarMixin):
    from gui2.pass1_add_view import Pass1AddView

    def __init__(
        self,
        ui: Pass1AddView,
        toolkit: ToolKit,
        pass1_auto_controller: Pass1AutoController,
    ) -> None:
        self.ui: Pass1AddView = ui
        self.db: DatabaseManager = toolkit.db_manager
        self.daily_log: DailyLog = toolkit.daily_log
        self.gui2pth: Gui2Paths = toolkit.paths
        self.additions_manager: AdditionsManager = toolkit.additions_manager
        self.username_manager: UsernameManager = toolkit.username_manager
        self.wordfinder_manager: WordFinderManager = toolkit.wordfinder_manager
        self.pass1_auto_controller = pass1_auto_controller

        self.pass1_books = sutta_central_books
        self.pass1_books_list = [k for k in self.pass1_books]
        self.book_to_process: str | None = None

        self.auto_processed_dict: dict[str, dict[str, str]] = {}
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
        self.auto_processed_dict = self.pass1_auto_controller.get_auto_processed_dict(
            self.book_to_process
        )
        if not self.auto_processed_dict:
            self.ui.update_message("file not found or empty.")
            self.auto_processed_dict_copy = {}
            self.auto_processed_iter = iter([])
            self.ui.update_remaining(0)
            return

        # dict will change size, so work on a copy
        self.auto_processed_dict_copy = self.auto_processed_dict.copy()
        self.auto_processed_iter = iter(self.auto_processed_dict_copy.items())
        self.ui.update_remaining(len(self.auto_processed_dict))

    def get_next_item(self):
        if self.book_to_process is None:
            self.ui.update_message("Please select a book to process first.")
            return False
        try:
            self.word_in_text, self.sentence_data = next(self.auto_processed_iter)
            # Update from the current file state to show accurate remaining count
            current_dict = self.pass1_auto_controller.get_auto_processed_dict(
                self.book_to_process
            )
            self.ui.update_remaining(len(current_dict))
            print(self.word_in_text)
            print(self.sentence_data)
            return True
        except StopIteration:
            # Update from the current file state when no more items
            current_dict = self.pass1_auto_controller.get_auto_processed_dict(
                self.book_to_process
            )
            self.ui.update_remaining(len(current_dict))
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

    def make_dpd_headword_and_add_to_db(self):
        # Collect data from UI fields into a dictionary
        field_data: dict[str, str] = {
            field_name: field.value or ""
            for field_name, field in self.ui.dpd_fields.fields.items()
            if hasattr(DpdHeadword, field_name)
        }
        comment = self.ui.dpd_fields.get_field("comment").value or ""

        # Create the DpdHeadword object using the imported function
        new_word = make_dpd_headword_from_dict(field_data)

        # Track if this is a new word or an update for logging purposes
        already_in_db = bool(new_word.id)

        # Check if this is an existing word loaded from history (has an ID)
        if already_in_db:
            # Update existing word - keep the same ID
            new_word.origin = "pass1"
            committed, message = self.db.update_word_in_db(new_word)
        else:
            # Create new word - assign new ID
            new_word.id = self.db.get_next_id()
            new_word.origin = "pass1"

            # add to additions
            if self.username_manager.is_not_primary():
                self.additions_manager.add_additions(new_word, comment)

            # add to db
            committed, message = self.db.add_word_to_db(new_word)

        if committed:
            # open in browser
            request_dpd_server(new_word.id)

            # Only increment daily log for new words, not re-edited words from history
            if not already_in_db:
                self.daily_log.increment("pass1")

            # Add to history
            self.ui.history_manager.add_item(
                new_word.id, new_word.lemma_1
            )  # Use ui's history_manager
            self.ui._update_history_dropdown()

            self.remove_word_and_save_json()
            self.ui.clear_all_fields()

            self.db.get_all_lemma_1_and_lemma_clean()
            is_next_item = self.get_next_item()
            if is_next_item:
                self.load_into_gui()
                self.ui.update_message(
                    f"{self.ui.dpd_fields.fields['lemma_1'].value} loaded"
                )
            else:
                self.ui.clear_all_fields()
        else:
            self.ui.update_message(
                f"""commit failed for {self.ui.dpd_fields.fields["lemma_1"].value}\n{message}"""
            )

    def remove_word_and_save_json(self):
        # Only remove from auto-processed dict if word_in_text exists
        # (i.e., when processing from a book, not when loading from history)
        if hasattr(self, "word_in_text") and self.word_in_text:
            self.pass1_auto_controller.remove_word(
                self.book_to_process, self.word_in_text
            )
            # Update the auto_processed_dict to reflect the removal
            self.auto_processed_dict = (
                self.pass1_auto_controller.get_auto_processed_dict(self.book_to_process)
            )
            self.ui.update_remaining(len(self.auto_processed_dict))
            self.ui.update_message(f"{self.word_in_text} deleted")
