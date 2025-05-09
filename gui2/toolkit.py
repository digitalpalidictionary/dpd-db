import flet as ft


class ToolKit:
    def __init__(self, page: ft.Page):
        from gui2.ai_search import AiSearchPopup
        from gui2.appbar_updater import AppBarUpdater
        from gui2.daily_log import DailyLog
        from gui2.database_manager import DatabaseManager
        from gui2.history import HistoryManager
        from gui2.test_manager import GuiTestManager
        from tools.ai_manager import AIManager
        from tools.hyphenations import HyphenationFileManager
        from tools.sandhi_contraction import SandhiContractionFinder
        from gui2.paths import Gui2Paths

        self.page: ft.Page = page

        # Managers with no ToolKit internal dependencies (or only page)
        self.paths: Gui2Paths = Gui2Paths()
        self.test_manager: GuiTestManager = GuiTestManager()
        self.sandhi_manager: SandhiContractionFinder = SandhiContractionFinder()
        self.hyphenation_manager: HyphenationFileManager = HyphenationFileManager()
        self.history_manager: HistoryManager = HistoryManager(self)
        self.ai_manager: AIManager = AIManager()
        self.db_manager: DatabaseManager = DatabaseManager()

        # Initialize DB parts needed early
        self.db_manager.pre_initialize_gui_data()

        # Managers with dependencies on other managers or page
        self.appbar_updater: AppBarUpdater = AppBarUpdater(self.page)
        self.daily_log: DailyLog = DailyLog(self)
        self.ai_search_popup: AiSearchPopup = AiSearchPopup(self)
