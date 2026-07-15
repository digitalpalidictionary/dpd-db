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
from tools.cst_source import (
    CstSourceSuttaExample,
)
from tools.cst_source.corpus_index import CstSourceIndex
from tools.goldendict_tools import open_in_goldendict


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
        self._cst_index: CstSourceIndex | None = None
        self.sc_book: str = ""
        self.all_cst_words: list[str] = []
        self.missing_examples_dict: dict[
            str, list[SuttaCentralSegment] | list[CstSourceSuttaExample]
        ] = {}
        self.word_in_text: str = ""
        self.headwords: list[DpdHeadword] = []
        self.headword_index: int = -1
        # in-comps mode: compound word in queue -> its components missing examples
        self.in_comps: bool = False
        self.comps_components: dict[str, list[str]] = {}
        # headword id -> component word it came from (for match recording)
        self.entry_headword_sources: dict[int, str] = {}

    def load_data(self) -> None:
        """Load database data only when needed."""
        if not self._data_loaded:
            self.db.make_pass2_lists()
            self._data_loaded = True

    def find_words_with_missing_examples(
        self, book: str, paths: Gui2Paths, in_comps: bool = False
    ):
        self.db.make_pass2_lists()
        self.in_comps = in_comps
        self.comps_components = {}
        self.entry_headword_sources = {}
        if in_comps:
            self.db.make_compound_components_map()
        self.file_manager = Pass2PreFileManager(book, paths)
        self.sc_book = sutta_central_books[book].sc_book
        self.cst_books = sutta_central_books[book].cst_books
        self._cst_index = None
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

    def is_missing_example(self, word: str) -> bool:
        return (
            (
                word in self.db.all_inflections_missing_example
                or word in self.db.all_decon_no_headwords
            )
            # and word not in self.db.sandhi_ok_list
            and word not in self.variant_readings.variants_dict
            and word not in self.spelling_mistakes.spelling_mistakes_dict
            and word not in self.file_manager.unmatched
            and word not in self.file_manager.matched
        )

    def make_all_words_dict(self):
        for word in self.all_cst_words:
            if self.is_missing_example(word):
                self.missing_examples_dict[word] = []
            if self.in_comps:
                self.add_comps_entry(word)

    def add_sc_words(self):
        for word, segments in self.sutta_central_books[self.sc_book].word_dict.items():
            if self.is_missing_example(word):
                self.missing_examples_dict[word] = segments
            if self.in_comps:
                self.add_comps_entry(word)

    def add_comps_entry(self, word: str) -> None:
        """In-comps mode: any book compound with components still missing
        examples becomes a work item at its place in the text — regardless
        of whether the compound itself has an example or was already
        processed. The gate is on the component: it must be missing an
        example and not yet decided on (matched/unmatched)."""

        if not word or word in self.comps_components:
            return
        components = self.db.compound_components_map.get(word)
        if not components:
            return
        missing = [
            c
            for c in components
            if self.is_missing_example(c)
            # a No on a sub word hides only this compound + sub word pair
            and f"{word} + {c}" not in self.file_manager.unmatched
        ]
        if not missing:
            return
        self.comps_components[word] = missing
        self.missing_examples_dict.setdefault(word, [])

    def load_next_word(self):
        while True:
            if not self.missing_examples_dict:
                self.ui.clear_all_fields()
                self.ui.update_message("No more words to process.")
                return

            self.word_in_text = next(iter(self.missing_examples_dict))
            self.ui.update_word_in_text(self.word_in_text)
            added = len(self.file_manager.matched) + len(self.file_manager.new_word)
            processed = self.daily_log.get_count("pass2_pre")
            self.ui.update_preprocessed_count(
                f"Added: {added}  Processed: {processed}  Remaining: {len(self.missing_examples_dict)}"
            )
            self.headwords = self.get_entry_headwords(self.word_in_text)

            # Skip words with no headwords (empty results from DB)
            while self.headwords and self.headwords[0] is None:
                self.missing_examples_dict.pop(self.word_in_text, None)
                if not self.missing_examples_dict:
                    self.ui.clear_all_fields()
                    self.ui.update_message("No more words to process.")
                    return
                self.word_in_text = next(iter(self.missing_examples_dict))
                self.headwords = self.get_entry_headwords(self.word_in_text)

            if not self.headwords:
                self.missing_examples_dict.pop(self.word_in_text)
                continue

            if not self.missing_examples_dict[self.word_in_text]:
                self.get_cst_examples()
            self.headword_index = -1
            self.load_next_headword()
            return

    def get_entry_headwords(self, word: str) -> list[DpdHeadword]:
        """The compound's own missing-example headwords, plus — in comps
        mode — the headwords of its components that are missing examples.
        Records which component each extra headword came from, so Yes/No
        decisions are saved under the component word."""
        self.entry_headword_sources = {}
        headwords = self.db.get_headwords(word)
        for component in self.comps_components.get(word, []):
            for hw in self.db.get_headwords(component):
                if all(h is None or h.id != hw.id for h in headwords):
                    headwords.append(hw)
                    self.entry_headword_sources[hw.id] = component
        return headwords

    def current_headword(self) -> DpdHeadword | None:
        """The headword under review, or None if the index is stale
        (double-click race, or a click after the queue is exhausted)."""
        if 0 <= self.headword_index < len(self.headwords):
            return self.headwords[self.headword_index]
        return None

    def current_source_word(self) -> str:
        """The word to record a Yes/No decision under: the component word
        for a component headword, otherwise the word in the text."""
        if 0 <= self.headword_index < len(self.headwords):
            headword = self.headwords[self.headword_index]
            if headword is not None:
                return self.entry_headword_sources.get(headword.id, self.word_in_text)
        return self.word_in_text

    def current_unmatched_key(self) -> str:
        """The key a No is recorded under: `compound + sub word` for a
        component headword, so the sub word still comes up in other
        compounds; the plain word otherwise."""
        source = self.current_source_word()
        if source != self.word_in_text:
            return f"{self.word_in_text} + {source}"
        return source

    def display_word_in_text(self) -> str:
        """Plain word for the word's own headwords; `[compound] sub word`
        when the current headword belongs to a component."""
        source = self.current_source_word()
        if source != self.word_in_text:
            return f"[{self.word_in_text}] {source}"
        return self.word_in_text

    def highlight_term_for(self, text: str) -> str:
        """The term to highlight in an example sentence: the sub word when
        reviewing a component headword, shortened from the end until the
        sentence contains it; the word in text unmodified otherwise."""
        word = self.current_source_word()
        if word == self.word_in_text:
            return word
        while word and word not in text:
            word = word[:-1]
        return word

    def get_cst_examples(self):
        if self.word_in_text:
            index = self._cst_index
            if index is None:
                index = CstSourceIndex(self.cst_books)
                self._cst_index = index
            regex_word_in_text = rf"\b{self.word_in_text}\b"
            self.missing_examples_dict[self.word_in_text] = index.find_examples(
                regex_word_in_text
            )
        else:
            self.ui.update_message("word_in_text is empty!")

    def load_next_headword(self):
        if self.headword_index + 1 >= len(self.headwords):
            self.missing_examples_dict.pop(self.word_in_text)
            self.daily_log.increment("pass2_pre")
            self.load_next_word()
            return

        self.headword_index += 1
        headword = self.headwords[self.headword_index]
        self.ui.update_word_in_text(self.display_word_in_text())
        self.ui.update_message("")

        examples_list = self.missing_examples_dict[self.word_in_text]
        examples_list = self.clean_examples_list(examples_list)
        examples_controls = self.ui.make_examples_list(examples_list)
        self.ui.headword_lemma_1_field.value = headword.lemma_1
        self.ui.headword_pos_field.value = headword.pos
        self.ui.headword_meaning_field.value = (
            f"{headword.meaning_combo} [{headword.construction_summary}]"
        )
        self.ui.update_examples(examples_controls)

        self.ui.page.update()
        open_in_goldendict(str(headword.id))

    def clean_examples_list(
        self, examples_list: list[SuttaCentralSegment] | list[CstSourceSuttaExample]
    ) -> list[SuttaCentralSegment] | list[CstSourceSuttaExample]:
        """Clean the examples list by removing all types of inverted commas and quotation marks."""

        cleaned_list = []
        for i in examples_list:
            if isinstance(i, SuttaCentralSegment):
                # Create a new instance with cleaned pali field
                cleaned_i = SuttaCentralSegment(
                    i.segment, self.clean_quotes(i.pali), i.english
                )
                cleaned_list.append(cleaned_i)
            elif isinstance(i, CstSourceSuttaExample):
                # Create a new instance with cleaned example field
                cleaned_i = CstSourceSuttaExample(
                    i.source, i.sutta, self.clean_quotes(i.example)
                )
                cleaned_list.append(cleaned_i)
        return cleaned_list

    def clean_quotes(self, text: str) -> str:
        """Remove all types of quotation marks from text."""
        # Straight quotes
        text = text.replace('"', "").replace("'", "")
        # Curly quotes
        text = text.replace("“", "").replace("”", "").replace("‘", "").replace("’", "")
        return text
