import json

from rich import print

from db.models import DpdHeadword
from gui2.class_books import (
    SuttaCentralSegment,
    SuttaCentralSource,
    sutta_central_books,
)
from gui2.class_daily_log import DailyLog
from gui2.class_database import DatabaseManager
from gui2.class_paths import Gui2Paths
from gui2.class_spelling import SpellingMistakesFileManager
from gui2.class_variants import VariantReadingFileManager
from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_source_sutta_example import (
    CstSourceSuttaExample,
    find_cst_source_sutta_example,
)
from tools.goldendict_tools import open_in_goldendict_os
from tools.printer import printer as pr


class Pass2PreprocessController:
    def __init__(self, ui, db: DatabaseManager) -> None:
        from gui2.tab_pass2_pre_view import Pass2PreProcessView

        self.ui: Pass2PreProcessView = ui
        self.db = db
        self.db.make_pass2_lists()
        self.file_manager: Pass2PreFileManager
        self.log = DailyLog()

        self.variant_readings = VariantReadingFileManager()
        self.spelling_mistakes = SpellingMistakesFileManager()

        self.sutta_central_books: dict[str, SuttaCentralSource] = sutta_central_books
        self.sutta_central_books_list = [k for k in self.sutta_central_books]

        self.cst_books: list[str]
        self.sc_book: str

        self.all_cst_words: list[str] = []
        self.missing_examples_dict: dict[
            str, list[SuttaCentralSegment] | list[CstSourceSuttaExample]
        ] = {}

        self.word_in_text: str
        self.headwords: list[DpdHeadword]
        self.headword_index: int = -1

    def find_words_with_missing_examples(self, book: str):
        self.file_manager = Pass2PreFileManager(book)
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
            word in self.db.all_inflections_missing_example
            and word not in self.db.sandhi_ok_list
            and word not in self.variant_readings.variants_dict
            and word not in self.spelling_mistakes.spelling_mistakes_dict
            and word not in self.file_manager.no
            and word not in self.file_manager.yes
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
        self.ui.update_preprocessed_count(f"{len(self.missing_examples_dict)}")
        self.headwords = self.db.get_headwords(self.word_in_text)
        if not self.missing_examples_dict[self.word_in_text]:
            self.get_cst_examples()
        self.headword_index = -1
        self.load_next_headword()

    def get_cst_examples(self):
        examples: list[CstSourceSuttaExample] = []
        for book in self.cst_books:
            examples.extend(find_cst_source_sutta_example(book, self.word_in_text))
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
    no: dict[str, int]
    yes: dict[str, dict[str, int | tuple[str, str, str]]]
    new: dict[str, tuple]

    def __init__(self, book: str) -> None:
        self.gui2pth = Gui2Paths()
        self._json_path = self.gui2pth.gui2_data_path / f"pass2_pre_{book}.json"
        self.no: dict[str, int] = {}
        self.yes: dict[str, dict[str, int | tuple[str, str, str]]] = {}
        self.new: dict[str, tuple] = {}
        self.load_data()

    def load_data(self) -> bool:
        """Loads the manager's state from a JSON file."""

        if self._json_path.exists():
            try:
                with open(self._json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.no = data.get("no", {})
                    self.yes = data.get("yes", {})
                    self.new = data.get("new", {})
                pr.green_title(f"Loaded pass2_pre data from {self._json_path}")
                return True
            except json.JSONDecodeError as e:
                pr.red(f"Error loading pass2_pre data (invalid JSON): {e}")
                self.no = {}
                self.yes = {}
                self.new = {}
                return False
            except Exception as e:
                pr.red(f"Unexpected error loading data: {e}")
                self.no = {}
                self.yes = {}
                self.new = {}
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
                    {"no": self.no, "yes": self.yes, "new": self.new},
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
            pr.green_title(f"Saved pass2_pre data to {self._json_path}")
        except IOError as e:
            pr.red(f"Error saving pass2_pre data: {e}")
        except Exception as e:
            pr.red(f"Unexpected error saving data: {e}")

    def update_no(
        self,
        word_in_text: str,
        headword_id: int,
    ) -> str:
        """Adds or updates an entry in the 'no' dictionary."""

        self.no[word_in_text] = headword_id
        self.save_data()
        message = f"Updated 'no' for '{word_in_text}' with id {headword_id}"
        return message

    def update_yes(
        self,
        word_in_text: str,
        headword_id: int,
        sentence: SuttaCentralSegment | CstSourceSuttaExample,
    ) -> str:
        """Adds or updates an entry in the 'yes' dictionary."""

        self.yes[word_in_text] = {
            "id": headword_id,
            "sentence": sentence,
        }
        self.save_data()
        message = f"Updated 'yes' for '{word_in_text}' with id {headword_id}"
        return message

    def update_new(
        self,
        word_in_text: str,
        sentence_data: SuttaCentralSegment | CstSourceSuttaExample,
    ) -> str:
        """Adds or updates an entry in the 'new' dictionary."""

        self.new[word_in_text] = sentence_data
        self.save_data()
        message = f"Updated 'new' for '{word_in_text}'"
        return message

    def remove_yes_item(self, word_in_text: str) -> str:
        """Removes an entry from the 'yes' dictionary and saves the data."""
        if word_in_text in self.yes:
            self.yes.pop(word_in_text)
            self.save_data()
            message = f"Removed '{word_in_text}' from 'yes' items"
            return message
        return f"'{word_in_text}' not found in 'yes' items"
