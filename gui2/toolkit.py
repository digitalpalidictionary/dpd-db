import flet as ft

from gui2.wordfinder_popup import WordFinderPopup
from tools.paths import ProjectPaths


class ToolKit:
    def __init__(self, page: ft.Page):
        from db_tests.db_tests_manager import DbTestManager
        from gui2.additions_manager import AdditionsManager
        from gui2.ai_search import AiSearchPopup
        from gui2.appbar_updater import AppBarUpdater
        from gui2.corrections_manager import CorrectionsManager
        from gui2.daily_log import DailyLog
        from gui2.database_manager import DatabaseManager
        from gui2.filter_presets_manager import FilterPresetsManager
        from gui2.history import HistoryManager
        from gui2.pass2_exceptions import Pass2ExceptionsFileManager
        from gui2.pass2_pre_new_word_manager import Pass2NewWordManager
        from gui2.paths import Gui2Paths
        from gui2.sandhi_files_manager import SandhiFileManager
        from gui2.spelling import SpellingMistakesFileManager
        from gui2.test_manager import GuiTestManager
        from gui2.user import UsernameManager
        from gui2.variants import VariantReadingFileManager
        from tools.ai_manager import AIManager
        from tools.bold_definitions_search import BoldDefinitionsSearchManager
        from tools.hyphenations import HyphenationFileManager
        from tools.sandhi_contraction import SandhiContractionManager
        from tools.wordfinder_manager import WordFinderManager

        self.page: ft.Page = page

        # Managers with no ToolKit internal dependencies (or only page)
        self.project_paths = ProjectPaths()
        self.paths: Gui2Paths = Gui2Paths()
        self.db_test_manager: DbTestManager = DbTestManager()
        self.test_manager: GuiTestManager = GuiTestManager(self)
        self.sandhi_manager: SandhiContractionManager = SandhiContractionManager()

        self.hyphenation_manager: HyphenationFileManager = HyphenationFileManager()
        self.history_manager: HistoryManager = HistoryManager(self)
        self.ai_manager: AIManager = AIManager()
        self.db_manager: DatabaseManager = DatabaseManager()
        self.pass2_exceptions_manager: Pass2ExceptionsFileManager = (
            Pass2ExceptionsFileManager(self)
        )
        self.pass2_new_word_manager: Pass2NewWordManager = Pass2NewWordManager(self)
        self.username_manager: UsernameManager = UsernameManager(self.page)
        self.corrections_manager: CorrectionsManager = CorrectionsManager(self)
        self.filter_presets_manager: FilterPresetsManager = FilterPresetsManager(self)
        self.additions_manager: AdditionsManager = AdditionsManager(self)
        self.appbar_updater: AppBarUpdater = AppBarUpdater(self.page)
        self.daily_log: DailyLog = DailyLog(self)
        self.ai_search_popup: AiSearchPopup = AiSearchPopup(self)
        self.wordfinder_manager: WordFinderManager = WordFinderManager()
        self.wordfinder_popup: WordFinderPopup = WordFinderPopup(self)
        self.bold_definitions_search_manager: BoldDefinitionsSearchManager = BoldDefinitionsSearchManager()
        self.variants: VariantReadingFileManager = VariantReadingFileManager()
        self.spelling_mistakes: SpellingMistakesFileManager = (
            SpellingMistakesFileManager()
        )

        self.sandhi_files_manager: SandhiFileManager = SandhiFileManager(self)

        # Initialize DB parts needed early
        self.db_manager.pre_initialize_gui_data()
