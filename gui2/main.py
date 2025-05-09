import cProfile
import time
from pathlib import Path
import flet as ft

from gui2.appbar_updater import AppBarUpdater
from gui2.daily_log import DailyLog
from gui2.database_manager import DatabaseManager
from gui2.history import HistoryManager
from gui2.test_manager import GuiTestManager
from tools.fast_api_utils import start_dpd_server
from tools.ai_manager import AIManager
from tools.hyphenations import HyphenationFileManager
from tools.sandhi_contraction import SandhiContractionFinder
from gui2.ai_search import AiSearchPopup
from gui2.sandhi_find_replace_view import SandhiFindReplaceView


class App:
    def __init__(self, page: ft.Page):
        from gui2.pass2_add_view import Pass2AddView
        from gui2.pass1_auto_view import Pass1AutoView

        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_auto_view import Pass2AutoView
        from gui2.pass2_pre_view import Pass2PreProcessView

        self.page = page

        if page.theme is None:
            page.theme = ft.Theme()
        page.theme.font_family = "Inter"
        self.page.window.top = 0
        self.page.window.left = 0
        self.page.window.height = 1280
        self.page.window.width = 1375
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.on_keyboard_event = self.on_keyboard

        # Init all the managers
        self.appbar_updater = AppBarUpdater(self.page)
        self.daily_log = DailyLog(self.appbar_updater)
        self.test_manager = GuiTestManager()
        self.sandhi_manager = SandhiContractionFinder()
        self.hyphenation_manger = HyphenationFileManager()
        self.history_manager = HistoryManager()
        self.ai_manager = AIManager()
        self.global_ai_popup = AiSearchPopup(self.page, self.ai_manager)

        # database init
        self.db = DatabaseManager()
        self.db.pre_initialize_gui_data()

        page.appbar = ft.AppBar(
            title=ft.Text("dpd gui"),
            bgcolor=ft.Colors.LIGHT_BLUE_900,
            elevation=100,
            title_spacing=20,
            center_title=False,
            actions=[ft.Text(self.daily_log.get_counts())],
        )

        # Now create views
        self.pass1_auto_view: Pass1AutoView = Pass1AutoView(
            self.page,
            self.db,
            self.ai_manager,
        )

        self.pass1_add_view: Pass1AddView = Pass1AddView(
            self.page,
            self.db,
            self.daily_log,
            self.sandhi_manager,
            self.history_manager,
        )
        self.pass2_pre_view: Pass2PreProcessView = Pass2PreProcessView(
            self.page,
            self.db,
            self.daily_log,
        )
        self.pass2_auto_view: Pass2AutoView = Pass2AutoView(
            self.page, self.db, self.ai_manager
        )
        self.pass2_add_view: Pass2AddView = Pass2AddView(
            self.page,
            self.db,
            self.daily_log,
            self.test_manager,
            self.sandhi_manager,
            self.hyphenation_manger,
            self.history_manager,
            self.ai_manager,
        )

        self.sandhi_view = SandhiFindReplaceView(
            self.page, self.db, self.daily_log, self.sandhi_manager
        )

        self.build_ui()

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()
        elif e.key == "A" and e.ctrl and e.shift:
            self.global_ai_popup.open_popup()
        elif e.key == "W" and e.ctrl:
            if self.global_ai_popup.is_dialog_open():
                self.global_ai_popup.close_dialog()

    def tab_clicked(self, e: ft.ControlEvent) -> None:
        """Handles tab clicks."""

        # load pass_1 database
        if self.db.all_lemma_1 is None:
            self.db.initialize_db()

    def build_ui(self) -> None:
        """Constructs the main UI elements."""

        tabs: ft.Tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_click=self.tab_clicked,
            tabs=[
                ft.Tab(
                    text="Pass1Auto",
                    content=self.pass1_auto_view,
                ),
                ft.Tab(
                    text="Pass1Add",
                    content=self.pass1_add_view,
                ),
                ft.Tab(
                    text="Pass2Pre",
                    content=self.pass2_pre_view,
                ),
                ft.Tab(
                    text="Pass2Auto",
                    content=self.pass2_auto_view,
                ),
                ft.Tab(
                    text="Pass2Add",
                    content=self.pass2_add_view,
                ),
                ft.Tab(
                    text="Sandhi",
                    content=self.sandhi_view,
                ),
            ],
            expand=True,
        )
        self.page.add(tabs)
        self.page.update()


def main(page: ft.Page) -> None:
    # Enable/disable profiling
    enable_profiling = True
    profile_file = Path("gui2_profile.prof")

    if enable_profiling:
        profiler = cProfile.Profile()
        profiler.enable()

    # Time FastAPI server startup
    start_time = time.time()
    start_dpd_server()
    print(f"FastAPI server started in {time.time() - start_time:.2f}s")

    # Time App initialization
    start_time = time.time()
    App(page)
    print(f"App initialized in {time.time() - start_time:.2f}s")

    if enable_profiling:
        profiler.disable()
        profiler.dump_stats(str(profile_file))
        print(f"snakeviz {profile_file}")


if __name__ == "__main__":
    ft.app(target=main)
