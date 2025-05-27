import json

from rich import print

from db.models import DpdHeadword
from gui2.books import (
    SuttaCentralSegment,
    SuttaCentralSource,
    sutta_central_books,
)
from gui2.paths import Gui2Paths
from gui2.spelling import SpellingMistakesFileManager
from gui2.toolkit import ToolKit
from gui2.variants import VariantReadingFileManager
from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_source_sutta_example import (
    CstSourceSuttaExample,
    find_cst_source_sutta_example,
)
from tools.goldendict_tools import open_in_goldendict_os
from tools.printer import printer as pr


class Pass2PreController:
    def __init__(
        self,
        ui,
        toolkit: ToolKit,
    ) -> None:
        from gui2.pass2_pre_view import Pass2PreProcessView

        self.ui: Pass2PreProcessView = ui
        self.db = toolkit.db_manager
        self.daily_log = toolkit.daily_log
        self._data_loaded = False
        self.file_manager: Pass2PreFileManager

        self.variant_readings = VariantReadingFileManager()
        self.spelling_mistakes = SpellingMistakesFileManager()

        # Keep lightweight book list initialization
        self.sutta_central_books: dict[str, SuttaCentralSource] = sutta_central_books
        self.sutta_central_books_list = [k for k in self.sutta_central_books]

        # Initialize empty containers for data that will be loaded later
        self.cst_books: list[str] = []
        self.sc_book: str = ""
        self.all_cst_words: list[str] = []
        self.missing_examples_dict: dict[
            str, list[SuttaCentralSegment] | list[CstSourceSuttaExample]
        ] = {}
        self.word_in_text: str = ""
        self.headwords: list[DpdHeadword] = []
        self.headword_index: int = -1

    def load_data(self) -> None:
        """Load database data only when needed."""
        if not self._data_loaded:
            self.db.make_pass2_lists()
            self._data_loaded = True

    def find_words_with_missing_examples(self, book: str, paths: Gui2Paths):
        self.file_manager = Pass2PreFileManager(book, paths)
        self.sc_book = sutta_central_books[book].sc_book
        self.cst_books = sutta_central_books[book].cst_books
        self.get_all_cst_words()
        self.make_all_words_dict()
        self.add_sc_words()

    def get_all_cst_words(self):
        self.all_cst_words = make_cst_text_list(
            self.cst_books,
            niggahita="ṃ",
            dedupe=True,
            add_hyphenated_parts=True,
        )

    def is_missing_example(self, word: str):
        if (
            (
                word in self.db.all_inflections_missing_example
                or word in self.db.all_decon_no_headwords
            )
            and word not in self.db.sandhi_ok_list
            and word not in self.variant_readings.variants_dict
            and word not in self.spelling_mistakes.spelling_mistakes_dict
            and word not in self.file_manager.unmatched.keys()
            and word not in self.file_manager.matched
        ):
            return True
        else:
            return False

    def make_all_words_dict(self):
        for word in self.all_cst_words:
            if self.is_missing_example(word):
                self.missing_examples_dict[word] = []

    def add_sc_words(self):
        for word, segments in self.sutta_central_books[self.sc_book].word_dict.items():
            if self.is_missing_example(word):
                self.missing_examples_dict[word] = segments

    def load_next_word(self):
        if not self.missing_examples_dict:
            self.ui.update_message("No more words to process.")
            return

        self.word_in_text = list(self.missing_examples_dict.keys())[0]
        self.ui.update_word_in_text(self.word_in_text)
        self.ui.update_preprocessed_count(
            f"{len(self.file_manager.matched)} / {len(self.missing_examples_dict)}"
        )
        self.headwords = self.db.get_headwords(self.word_in_text)
        if not self.missing_examples_dict[self.word_in_text]:
            self.get_cst_examples()
        self.headword_index = -1
        self.load_next_headword()

    def get_cst_examples(self):
        examples: list[CstSourceSuttaExample] = []
        for book in self.cst_books:
            regex_word_in_text = rf"\b{self.word_in_text}\b"
            examples.extend(find_cst_source_sutta_example(book, regex_word_in_text))
        self.missing_examples_dict[self.word_in_text] = examples

    def load_next_headword(self):
        if self.headword_index + 1 >= len(self.headwords):
            self.missing_examples_dict.pop(self.word_in_text)
            self.load_next_word()
            return

        self.headword_index += 1
        headword = self.headwords[self.headword_index]
        self.ui.update_message("")

        examples_list = self.missing_examples_dict[self.word_in_text]
        examples_controls = self.ui.make_examples_list(examples_list)
        self.ui.headword_lemma_1_field.value = headword.lemma_1
        self.ui.headword_pos_field.value = headword.pos
        self.ui.headword_meaning_field.value = (
            f"{headword.meaning_combo} [{headword.construction_summary}]"
        )
        self.ui.update_examples(examples_controls)

        self.ui.page.update()
        open_in_goldendict_os(str(headword.id))


class Pass2PreFileManager:
    def __init__(self, book: str, paths: Gui2Paths) -> None:
        self._gui2pth: Gui2Paths = paths
        self._json_path = self._gui2pth.gui2_data_path / f"pass2_pre_{book}.json"
        self.unmatched: dict[str, list[int]] = {}
        self.matched: dict[str, dict[str, int | tuple[str, str, str]]] = {}
        self.new_word: dict[str, tuple] = {}
        self.processed: list[str] = []
        self.load_data()

    def load_data(self) -> bool:
        """Loads the manager's state from a JSON file."""

        if self._json_path.exists():
            try:
                with open(self._json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.unmatched = data.get("unmatched", {})
                    self.matched = data.get("matched", {})
                    self.new_word = data.get("new_word", {})
                    self.processed = data.get("processed", [])
                return True
            except json.JSONDecodeError as e:
                pr.red(f"Error loading pass2_pre data (invalid JSON): {e}")
                self.unmatched = {}
                self.matched = {}
                self.new_word = {}
                return False
            except Exception as e:
                pr.red(f"Unexpected error loading data: {e}")
                self.unmatched = {}
                self.matched = {}
                self.new_word = {}
                return False
        else:
            print(f"[yellow]pass2_pre data file not found at {self._json_path}")
            return False

    def save_data(self) -> None:
        """Saves the manager's current state to a JSON file."""
        try:
            self._json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "unmatched": self.unmatched,
                        "matched": self.matched,
                        "new_word": self.new_word,
                        "processed": self.processed,
                    },
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
        except IOError as e:
            pr.red(f"Error saving pass2_pre data: {e}")
        except Exception as e:
            pr.red(f"Unexpected error saving data: {e}")

    def update_unmatched(
        self,
        word_in_text: str,
        headword_id: int,
    ) -> str:
        """Adds or updates an entry in the 'unmatched' dictionary."""

        if word_in_text not in self.unmatched:
            self.unmatched[word_in_text] = []
        if headword_id not in self.unmatched[word_in_text]:
            self.unmatched[word_in_text].append(headword_id)
        self.save_data()
        message = f"Updated 'unmatched' for '{word_in_text}' with id {headword_id}"
        return message

    def update_matched(
        self,
        word_in_text: str,
        headword_id: int,
        sentence: SuttaCentralSegment | CstSourceSuttaExample,
    ) -> str:
        """Adds or updates an entry in the 'matched' dictionary."""

        self.matched[word_in_text] = {
            "id": headword_id,
            "sentence": sentence,
        }
        self.save_data()
        message = f"Updated 'matched' for '{word_in_text}' with id {headword_id}"
        return message

    def update_new_word(
        self,
        word_in_text: str,
        sentence_data: SuttaCentralSegment | CstSourceSuttaExample,
    ) -> str:
        """Adds or updates an entry in the 'new_word' dictionary."""

        self.new_word[word_in_text] = sentence_data
        self.save_data()
        message = f"Updated 'new_word' for '{word_in_text}'"
        return message

    def move_matched_item_to_processed(self, word_in_text: str) -> str:
        """
        1. Removes an entry from the 'matched' dictionary,
        2. updates the processed dictionary
        3. and saves the data.
        """

        if word_in_text in self.matched:
            self.matched.pop(word_in_text)
            self.processed.append(word_in_text)
            self.save_data()
            message = f"Moved '{word_in_text}' from 'matched' to 'processed'"
            return message
        return f"'{word_in_text}' not found in 'matched' items"
