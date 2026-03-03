import cProfile
import time
from pathlib import Path

import flet as ft

from gui2.roots_tab_view import RootsTabView
from gui2.sandhi_find_replace_view import SandhiFindReplaceView
from gui2.sandhi_view import SandhiView
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
        from gui2.bold_search_view import BoldSearchView
        from gui2.tests_tab_view import TestsTabView
        from gui2.translations_view import TranslationsView

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

        appbar_actions: list[ft.Control] = [
            ft.Text(self.toolkit.daily_log.get_counts())
        ]
        if self.toolkit.username_manager.is_not_primary():
            appbar_actions.extend(
                [
                    ft.VerticalDivider(),
                    ft.TextButton(
                        "Submit Data",
                        icon=ft.Icons.CLOUD_UPLOAD,
                        on_click=self._on_submit_data,
                    ),
                    ft.TextButton(
                        "Update",
                        icon=ft.Icons.REFRESH,
                        on_click=self._on_check_updates,
                    ),
                ]
            )

        page.appbar = ft.AppBar(
            title=ft.Text("dpd gui"),
            bgcolor=ft.Colors.LIGHT_BLUE_900,
            elevation=100,
            title_spacing=20,
            center_title=False,
            actions=appbar_actions,
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
        self.sandhi_view2 = SandhiView(self.page, self.toolkit)
        self.filter_tab_view = FilterTabView(self.page, self.toolkit)
        self.translations_view = TranslationsView(self.page, self.toolkit)
        self.bold_search_view = BoldSearchView(self.page, self.toolkit)
        self.roots_view = RootsTabView(self.page, self.toolkit)

        self.build_ui()

        self.toolkit.username_manager.get_username()

    def _on_submit_data(self, e: ft.ControlEvent) -> None:
        """Handle Submit Data button click."""
        from scripts.onboarding.data_submission import submit_data

        result = submit_data(Path.cwd())
        dialog = ft.AlertDialog(
            title=ft.Text("Submit Data"),
            content=ft.Text(result.message),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.page.close(dialog)),
            ],
        )
        self.page.open(dialog)

    def _on_check_updates(self, e: ft.ControlEvent) -> None:
        """Handle Update button click."""
        from scripts.onboarding.contributor_update import update_environment

        summary = update_environment(Path.cwd())
        dialog = ft.AlertDialog(
            title=ft.Text("Update Complete"),
            content=ft.Text(summary),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.page.close(dialog)),
            ],
        )
        self.page.open(dialog)

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()
        elif e.key == "A" and e.ctrl and e.shift:
            self.toolkit.ai_search_popup.open_popup()
        elif e.key == "F" and e.ctrl:
            self.toolkit.wordfinder_popup.open_popup(self._get_current_lemma())
        elif e.key == "W" and e.ctrl:
            # Universal close key - close any open dialog
            if self.toolkit.ai_search_popup.is_dialog_open():
                self.toolkit.ai_search_popup.close_dialog()
            elif self.toolkit.wordfinder_popup.is_dialog_open():
                self.toolkit.wordfinder_popup.close_dialog()
        elif e.key == "Arrow Left" and e.alt:
            if self.tabs.selected_index > 0:
                self.tabs.selected_index -= 1
                self.page.update()
        elif e.key == "Arrow Right" and e.alt:
            if self.tabs.selected_index < len(self.tabs.tabs) - 1:
                self.tabs.selected_index += 1
                self.page.update()

    def _get_current_lemma(self) -> str:
        """Return lemma_1 from the active add-view, or empty string."""
        tab_to_view = {
            3: self.pass1_add_view,
            6: self.pass2_add_view,
        }
        view = tab_to_view.get(self.tabs.selected_index)
        if view is None:
            return ""
        try:
            field = view.dpd_fields.get_field("lemma_1")
            return (field.value or "").strip() if field else ""
        except Exception:
            return ""

    def tab_clicked(self, e: ft.ControlEvent) -> None:
        """Handles tab clicks."""

        # load pass_1 database
        if self.toolkit.db_manager.all_lemma_1 is None:
            self.toolkit.db_manager.initialize_db()

    def build_ui(self) -> None:
        """Constructs the main UI elements."""

        self.tabs: ft.Tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_click=self.tab_clicked,
            tabs=[
                ft.Tab(
                    text="Global",
                    content=self.global_view,
                ),
                ft.Tab(
                    text="Transl",
                    content=self.translations_view,
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
                    text="Sandhi",
                    content=self.sandhi_view2,
                ),
                ft.Tab(
                    text="DB",
                    content=self.filter_tab_view,
                ),
                ft.Tab(
                    text="Tests",
                    content=self.tests_tab_view,
                ),
                ft.Tab(
                    text="Bold Search",
                    content=self.bold_search_view,
                ),
                ft.Tab(
                    text="√",
                    content=self.roots_view,
                ),
            ],
            expand=True,
        )
        self.page.add(self.tabs)
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
