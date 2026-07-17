from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import flet as ft

from tools.configger import config_read
from tools.paths import ProjectPaths

if TYPE_CHECKING:
    from gui2.additions_manager import AdditionsManager
    from gui2.corrections_manager import CorrectionsManager
    from gui2.wordfinder_popup import WordFinderPopup
    from tools.ai_manager import AIManager
    from tools.bold_definitions_search import BoldDefinitionsSearchManager
    from tools.wordfinder_manager import WordFinderManager


class ToolKit:
    def __init__(self, page: ft.Page):
        from db_tests.db_tests_manager import DbTestManager
        from gui2.appbar_updater import AppBarUpdater
        from gui2.daily_log import DailyLog
        from gui2.database_manager import DatabaseManager
        from gui2.filter_presets_manager import FilterPresetsManager
        from gui2.history import HistoryManager
        from gui2.pass2_exceptions import Pass2ExceptionsFileManager
        from gui2.pass2_pre_new_word_manager import Pass2NewWordManager
        from gui2.paths import Gui2Paths
        from gui2.sandhi_files_manager import SandhiFileManager
        from gui2.see import SeeFileManager
        from gui2.spelling import SpellingMistakesFileManager
        from gui2.test_manager import GuiTestManager
        from gui2.user import UsernameManager
        from gui2.variants import VariantReadingFileManager
        from tools.proofreader import ProofreaderManager
        from tools.speech_marks import SpeechMarkManager

        self.page: ft.Page = page

        # Guards the lazy managers below: functools.cached_property has no
        # lock since Python 3.12, so the warm-up thread and a UI event
        # handler could each build their own instance. RLock because
        # wordfinder_popup's factory reads wordfinder_manager.
        self._lazy_lock = threading.RLock()
        self._lazy_cache: dict[str, Any] = {}

        # Managers with no ToolKit internal dependencies (or only page)
        self.project_paths = ProjectPaths()
        username = config_read("gui2", "username") or "1"
        self.paths: Gui2Paths = Gui2Paths.for_user(username)
        self.db_test_manager: DbTestManager = DbTestManager()
        self.test_manager: GuiTestManager = GuiTestManager(self)
        self.speech_marks_manager: SpeechMarkManager = SpeechMarkManager()

        self.history_manager: HistoryManager = HistoryManager(self)
        self.db_manager: DatabaseManager = DatabaseManager()
        self.pass2_exceptions_manager: Pass2ExceptionsFileManager = (
            Pass2ExceptionsFileManager(self)
        )
        self.pass2_new_word_manager: Pass2NewWordManager = Pass2NewWordManager(self)
        self.username_manager: UsernameManager = UsernameManager(self.page)
        self.filter_presets_manager: FilterPresetsManager = FilterPresetsManager(self)
        self.proofreader_manager: ProofreaderManager = ProofreaderManager(
            self.project_paths.proofreader_tsv_path
        )
        self.appbar_updater: AppBarUpdater = AppBarUpdater(self.page)
        self.daily_log: DailyLog = DailyLog(self)
        self.see_manager: SeeFileManager = SeeFileManager()
        self.variants: VariantReadingFileManager = VariantReadingFileManager()
        self.spelling_mistakes: SpellingMistakesFileManager = (
            SpellingMistakesFileManager()
        )

        self.sandhi_files_manager: SandhiFileManager = SandhiFileManager(self)

        # Initialize DB parts needed early
        self.db_manager.pre_initialize_gui_data()

    # Lazily constructed managers: each carries a real startup cost (74 MB
    # wordfinder JSON, six AI provider SDKs, a held DB session, contributor
    # file globs), so build on first access — the startup warm-up worker
    # touches them in the background so they are ready before first use.

    def _lazy[T](self, name: str, factory: Callable[[], T]) -> T:
        with self._lazy_lock:
            if name not in self._lazy_cache:
                self._lazy_cache[name] = factory()
            return self._lazy_cache[name]

    @property
    def ai_manager(self) -> AIManager:
        from tools.ai_manager import AIManager

        return self._lazy("ai_manager", AIManager)

    @property
    def wordfinder_manager(self) -> WordFinderManager:
        from tools.wordfinder_manager import WordFinderManager

        return self._lazy("wordfinder_manager", WordFinderManager)

    @property
    def bold_definitions_search_manager(self) -> BoldDefinitionsSearchManager:
        from tools.bold_definitions_search import BoldDefinitionsSearchManager

        return self._lazy(
            "bold_definitions_search_manager", BoldDefinitionsSearchManager
        )

    @property
    def additions_manager(self) -> AdditionsManager:
        from gui2.additions_manager import AdditionsManager

        return self._lazy("additions_manager", lambda: AdditionsManager(self))

    @property
    def corrections_manager(self) -> CorrectionsManager:
        from gui2.corrections_manager import CorrectionsManager

        return self._lazy("corrections_manager", lambda: CorrectionsManager(self))

    @property
    def wordfinder_popup(self) -> WordFinderPopup:
        from gui2.wordfinder_popup import WordFinderPopup

        return self._lazy("wordfinder_popup", lambda: WordFinderPopup(self))
