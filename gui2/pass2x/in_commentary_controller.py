"""Pass2x "in commentary" — GUI controller (stage 2).

Wraps the stage-1 matching pipeline in a Pass2Pre-style controller that walks the
user through each candidate word, its incomplete headword(s) and the example
sentences it appears in, persisting Yes/No choices in the same ``matched`` JSON
shape that Pass2Auto consumes.

Example sentences are sourced **just-in-time, per word** (not pre-scanned for the
whole ~18k candidate set), because a session only processes a handful of words —
``find_examples_for_word`` runs when each word becomes current, with no cap.

The matching layer is unchanged from stage 1: word→headwords comes from the
inflection map of incomplete headwords (``not (meaning_1 and source_1)``), not
from ``db.get_headwords``/``Lookup``.
"""

import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.pass2_pre_file_manager import Pass2PreFileManager
from gui2.pass2x.in_commentary_exceptions import InCommentaryExceptions
from gui2.pass2x.in_commentary_tui import (
    CommentarySource,
    Example,
    build_inflection_map,
    find_examples_for_word,
    harvest_commentary_words,
)
from gui2.toolkit import ToolKit
from tools.goldendict_tools import open_in_goldendict

HTML_TAG_RE: re.Pattern[str] = re.compile(r"<[^>]+>")
DAILY_LOG_KEY: str = "pass2x"


class Pass2xInCommentaryController:
    def __init__(self, ui, toolkit: ToolKit) -> None:
        from gui2.pass2x.in_commentary_view import Pass2xInCommentaryView

        self.ui: Pass2xInCommentaryView = ui
        self.toolkit: ToolKit = toolkit
        self.db = toolkit.db_manager
        self.daily_log = toolkit.daily_log
        self.project_paths = toolkit.project_paths

        self.exceptions: InCommentaryExceptions = InCommentaryExceptions(
            toolkit.paths.in_commentary_exceptions_path
        )
        self.file_manager: Pass2PreFileManager = Pass2PreFileManager(
            "in_commentary", toolkit.paths
        )

        # word -> incomplete headwords; word -> the commentary it came from
        self.resolved: dict[str, list[DpdHeadword]] = {}
        self.word_source: dict[str, CommentarySource] = {}
        # remaining words to process, and the current word's examples (JIT)
        self.word_queue: list[str] = []
        self.current_examples: list[Example] = []

        self.word_in_text: str = ""
        self.headwords: list[DpdHeadword] = []
        self.headword_index: int = -1

    # --- loading ---

    def load_in_commentary(self) -> None:
        """Harvest candidate words and build the work queue.

        Cheap relative to stage 1: only the commentary harvest and inflection map
        run here — the translations DB is *not* scanned. Example sentences are
        found per word in ``load_next_word``.
        """
        db_session = get_db_session(self.project_paths.dpd_db_path)
        words, word_source, _rows = harvest_commentary_words(db_session)
        inflection_map = build_inflection_map(db_session)
        db_session.close()

        self.word_source = word_source
        self.resolved = {
            word: inflection_map[word]
            for word in words
            if word in inflection_map and word not in self.exceptions
        }
        self.word_queue = [word for word in self.resolved if self._is_unprocessed(word)]

    def _is_unprocessed(self, word: str) -> bool:
        return (
            word not in self.file_manager.matched
            and word not in self.file_manager.unmatched
            and word not in self.file_manager.processed
        )

    def _commentary_example(self, word: str) -> Example:
        """Example #0 — the commentary the word was harvested from."""
        source = self.word_source[word]
        pali = HTML_TAG_RE.sub("", source.commentary).strip()
        return Example(
            source=f"commentary: {source.lemma_1}",
            paranum="",
            pali_raw=pali,
            english="",
            word=word,
            is_commentary=True,
        )

    # --- walking the queue ---

    def load_next_word(self) -> None:
        while self.word_queue:
            self.word_in_text = self.word_queue.pop(0)
            self.headwords = self.resolved.get(self.word_in_text, [])
            if not self.headwords:
                continue

            self.ui.update_word_in_text(self.word_in_text)
            self.ui.update_message("searching examples...")
            self.current_examples = [
                self._commentary_example(self.word_in_text),
                *find_examples_for_word(
                    self.project_paths.tipitaka_translation_db_path,
                    self.word_in_text,
                ),
            ]
            self._update_counter()
            self.headword_index = -1
            self.load_next_headword()
            return

        self.ui.clear_all_fields()
        self.ui.update_message("No more words to process.")

    def load_next_headword(self) -> None:
        if self.headword_index + 1 >= len(self.headwords):
            self.daily_log.increment(DAILY_LOG_KEY)
            self.load_next_word()
            return

        self.headword_index += 1
        headword = self.headwords[self.headword_index]
        self.ui.update_message("")

        examples_controls = self.ui.make_examples_list(self.current_examples)
        self.ui.headword_lemma_1_field.value = headword.lemma_1
        self.ui.headword_pos_field.value = headword.pos
        self.ui.headword_meaning_field.value = (
            f"{headword.meaning_combo} [{headword.construction_summary}]"
        )
        self.ui.update_examples(examples_controls)
        self.ui.page.update()
        open_in_goldendict(str(headword.id))

    def search_word(self, word: str) -> None:
        """Re-run the example search for a manually edited word, keeping the
        current headword(s). The commentary example is included only if the word
        was harvested (i.e. has a known source)."""
        word = word.strip()
        if not word:
            return
        self.word_in_text = word
        commentary = (
            [self._commentary_example(word)] if word in self.word_source else []
        )
        self.current_examples = commentary + find_examples_for_word(
            self.project_paths.tipitaka_translation_db_path, word
        )
        self.ui.update_examples(self.ui.make_examples_list(self.current_examples))
        hits = len(self.current_examples) - len(commentary)
        self.ui.update_message(f"{hits} example(s) for '{word}'")

    def skip_word(self, word: str) -> None:
        """Drop a word from the queue (used by the exceptions field)."""
        if word in self.word_queue:
            self.word_queue.remove(word)
        if word == self.word_in_text:
            self.load_next_word()

    def _update_counter(self) -> None:
        added = len(self.file_manager.matched)
        processed = self.daily_log.get_count(DAILY_LOG_KEY)
        self.ui.update_preprocessed_count(
            f"Added: {added}  Processed: {processed}  Remaining: {len(self.word_queue)}"
        )
