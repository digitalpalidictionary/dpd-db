import cProfile
import time
from pathlib import Path
import flet as ft

from gui2.class_appbar_updater import AppBarUpdater
from gui2.class_daily_log import DailyLog
from gui2.class_database import DatabaseManager
from tools.fast_api_utils import start_dpd_server


class App:
    def __init__(self, page: ft.Page):
        from gui2.tab_pass2_add_view import EditView
        from gui2.tab_pass1_auto_view import Pass1AutoView
        from gui2.tab_pass1_add_view import Pass1AddView
        from gui2.tab_pass2_auto_view import Pass2AutoView
        from gui2.tab_pass2_pre_view import Pass2PreProcessView

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

        # Instantiate AppBarUpdater first
        self.appbar_updater = AppBarUpdater(self.page)
        self.daily_log = DailyLog(self.appbar_updater)  # Pass updater to DailyLog

        page.appbar = ft.AppBar(
            title=ft.Text("dpd gui"),
            bgcolor=ft.Colors.LIGHT_BLUE_900,
            elevation=100,
            title_spacing=20,
            center_title=False,
            actions=[ft.Text(self.daily_log.get_counts())],
        )

        # initialize classes
        self.db = DatabaseManager()
        self.pass1_auto_view: Pass1AutoView = Pass1AutoView(self.page, self.db)
        self.pass1_add_view: Pass1AddView = Pass1AddView(
            self.page, self.db, self.daily_log
        )
        self.pass2_pre_view: Pass2PreProcessView = Pass2PreProcessView(
            self.page, self.db, self.daily_log
        )
        self.pass2_auto_view: Pass2AutoView = Pass2AutoView(self.page, self.db)
        self.pass2_add_view: EditView = EditView(self.page, self.db, self.daily_log)

        self.build_ui()

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

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
