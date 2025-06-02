from db.models import DpdHeadword
from gui2.books import (
    SuttaCentralSegment,
    SuttaCentralSource,
    sutta_central_books,
)
from gui2.pass2_pre_file_manager import Pass2PreFileManager
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
        self.pass2_exceptions_manager = toolkit.pass2_exceptions_manager

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
        if self.word_in_text:
            examples: list[CstSourceSuttaExample] = []
            for book in self.cst_books:
                regex_word_in_text = rf"\b{self.word_in_text}\b"
                examples.extend(find_cst_source_sutta_example(book, regex_word_in_text))
            self.missing_examples_dict[self.word_in_text] = examples
        else:
            self.ui.update_message("word_in_text is empty!")

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
