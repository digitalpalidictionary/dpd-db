import cProfile
import time
from pathlib import Path

import flet as ft

from gui2.sandhi_find_replace_view import SandhiFindReplaceView
from gui2.toolkit import ToolKit
from tools.fast_api_utils import start_dpd_server


class App:
    def __init__(self, page: ft.Page) -> None:
        from gui2.filter_tab_view import FilterTabView
        from gui2.global_tab_view import GlobalTabView
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass1_auto_view import Pass1AutoView
        from gui2.pass2_add_view import Pass2AddView
        from gui2.pass2_auto_view import Pass2AutoView
        from gui2.pass2_pre_view import Pass2PreProcessView
        from gui2.tests_tab_view import TestsTabView

        self.page = page

        page.theme = ft.Theme()
        page.theme.font_family = "Inter"
        self.page.window.top = 0
        self.page.window.left = 0
        self.page.window.height = 1280
        self.page.window.width = 1375
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.on_keyboard_event = self.on_keyboard

        # toolkit contains all the managers
        self.toolkit: ToolKit = ToolKit(self.page)

        page.appbar = ft.AppBar(
            title=ft.Text("dpd gui"),
            bgcolor=ft.Colors.LIGHT_BLUE_900,
            elevation=100,
            title_spacing=20,
            center_title=False,
            actions=[ft.Text(self.toolkit.daily_log.get_counts())],
        )

        # Now create views
        self.global_view: GlobalTabView = GlobalTabView(self.page, self.toolkit)
        self.pass1_auto_view: Pass1AutoView = Pass1AutoView(self.page, self.toolkit)
        self.pass1_add_view: Pass1AddView = Pass1AddView(
            self.page,
            self.toolkit,
            self.pass1_auto_view.controller,
        )
        self.pass2_pre_view: Pass2PreProcessView = Pass2PreProcessView(
            self.page, self.toolkit
        )
        self.pass2_auto_view: Pass2AutoView = Pass2AutoView(self.page, self.toolkit)
        self.pass2_add_view: Pass2AddView = Pass2AddView(self.page, self.toolkit)
        self.tests_tab_view: TestsTabView = TestsTabView(self.page, self.toolkit)
        self.sandhi_view = SandhiFindReplaceView(self.page, self.toolkit)
        self.filter_tab_view = FilterTabView(self.page, self.toolkit)

        self.build_ui()

        self.toolkit.username_manager.get_username()

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()
        elif e.key == "A" and e.ctrl and e.shift:
            self.toolkit.ai_search_popup.open_popup()
        elif e.key == "F" and e.ctrl:
            self.toolkit.wordfinder_popup.open_popup()
        elif e.key == "W" and e.ctrl:
            # Universal close key - close any open dialog
            if self.toolkit.ai_search_popup.is_dialog_open():
                self.toolkit.ai_search_popup.close_dialog()
            elif self.toolkit.wordfinder_popup.is_dialog_open():
                self.toolkit.wordfinder_popup.close_dialog()

    def tab_clicked(self, e: ft.ControlEvent) -> None:
        """Handles tab clicks."""

        # load pass_1 database
        if self.toolkit.db_manager.all_lemma_1 is None:
            self.toolkit.db_manager.initialize_db()

    def build_ui(self) -> None:
        """Constructs the main UI elements."""

        tabs: ft.Tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_click=self.tab_clicked,
            tabs=[
                ft.Tab(
                    text="Global",
                    content=self.global_view,
                ),
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
                    text="'",
                    content=self.sandhi_view,
                ),
                ft.Tab(
                    text="DB",
                    content=self.filter_tab_view,
                ),
                ft.Tab(
                    text="Tests",
                    content=self.tests_tab_view,
                ),
            ],
            expand=True,
        )
        self.page.add(tabs)
        self.page.update()


def main(page: ft.Page) -> None:
    # Enable/disable profiling
    enable_profiling = False
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
