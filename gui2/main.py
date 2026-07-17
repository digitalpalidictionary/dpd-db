import cProfile
import re
import threading
import time
from collections.abc import Callable
from pathlib import Path

import flet as ft

from gui2.ai_search_window import launch_ai_search_window
from gui2.compound_type_tab_view import CompoundTypeTabView
from gui2.roots_tab_view import RootsTabView
from gui2.sandhi_find_replace_view import SandhiFindReplaceView
from gui2.sandhi_view import SandhiView
from gui2.toolkit import ToolKit
from gui2.ui_utils import show_global_snackbar
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
        from gui2.pass2x.in_commentary_view import Pass2xInCommentaryView
        from gui2.bold_search_view import BoldSearchView
        from gui2.tests_tab_view import TestsTabView
        from gui2.translations_view import TranslationsView

        self.page = page
        self._db_init_started: bool = False
        # Guards _views/_mounted_tabs: the warm-up worker builds tabs in the
        # background while the user may click one on the UI thread.
        self._build_lock = threading.RLock()

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

        # Views are built off the UI thread by the warm-up worker (in
        # priority order) so the window paints instantly and every tab is
        # ready by the time it is clicked; clicking a not-yet-warmed tab
        # builds it on demand (see _view / _on_tab_activated). Each builder
        # is a thunk keyed by tab index; the Pass1Add view reuses the
        # Pass1Auto view's controller, so building it transparently builds
        # Pass1Auto first via _view(2).
        self._views: dict[int, ft.Control] = {}
        self._mounted_tabs: set[int] = set()
        self._view_builders: dict[int, Callable[[], ft.Control]] = {
            0: lambda: GlobalTabView(self.page, self.toolkit),
            1: lambda: TranslationsView(self.page, self.toolkit),
            2: lambda: Pass1AutoView(self.page, self.toolkit),
            3: lambda: Pass1AddView(self.page, self.toolkit, self._view(2).controller),
            4: lambda: Pass2PreProcessView(self.page, self.toolkit),
            5: lambda: Pass2xInCommentaryView(self.page, self.toolkit),
            6: lambda: Pass2AutoView(self.page, self.toolkit),
            7: lambda: Pass2AddView(self.page, self.toolkit),
            8: lambda: SandhiFindReplaceView(self.page, self.toolkit),
            9: lambda: SandhiView(self.page, self.toolkit),
            10: lambda: FilterTabView(self.page, self.toolkit),
            11: lambda: TestsTabView(self.page, self.toolkit),
            12: lambda: BoldSearchView(self.page, self.toolkit),
            13: lambda: RootsTabView(self.page, self.toolkit),
            14: lambda: CompoundTypeTabView(self.page, self.toolkit),
        }

        # Most-used tabs first so they are ready soonest.
        self._warmup_tab_order: list[int] = [
            7,
            4,
            5,
            6,
            2,
            3,
            1,
            12,
            10,
            8,
            9,
            11,
            13,
            14,
        ]

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
        """Handle Update button click with confirmation."""

        def _run_update(e: ft.ControlEvent) -> None:
            self.page.close(confirm_dialog)
            from scripts.onboarding.contributor_update import update_environment

            summary = update_environment(Path.cwd())
            result_dialog = ft.AlertDialog(
                title=ft.Text("Update Complete"),
                content=ft.Text(summary),
                actions=[
                    ft.TextButton(
                        "OK", on_click=lambda _: self.page.close(result_dialog)
                    ),
                ],
            )
            self.page.open(result_dialog)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ Warning"),
            content=ft.Text(
                "This will pull the latest code and may overwrite your "
                "local dpd.db with the latest release.\n\n"
                "A backup will be created automatically, but are you sure?"
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: self.page.close(confirm_dialog),
                ),
                ft.TextButton(
                    "Update",
                    on_click=_run_update,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(confirm_dialog)

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()
        elif e.key == "A" and e.ctrl and e.shift:
            launch_ai_search_window()
        elif e.key == "F" and e.ctrl:
            self.toolkit.wordfinder_popup.open_popup(self._get_current_lemma())
        elif e.key == "W" and e.ctrl:
            # Universal close key - close any open dialog
            if self.toolkit.wordfinder_popup.is_dialog_open():
                self.toolkit.wordfinder_popup.close_dialog()
        elif e.key == "S" and e.ctrl:
            tab = self.tabs.tabs[self.tabs.selected_index]
            view = tab.content
            # Ctrl+S saves table changes in tabs that support it
            if hasattr(view, "_on_save_changes"):
                view._on_save_changes(None)
            elif hasattr(view, "_save_changes_clicked"):
                view._save_changes_clicked(None)
        elif e.key == "Arrow Left" and e.alt:
            if self.tabs.selected_index > 0:
                self.tabs.selected_index -= 1
                self._on_tab_activated()
        elif e.key == "Arrow Right" and e.alt:
            if self.tabs.selected_index < len(self.tabs.tabs) - 1:
                self.tabs.selected_index += 1
                self._on_tab_activated()

    def _get_current_lemma(self) -> str:
        """Return lemma_clean from the active add-view, or empty string."""
        index = self.tabs.selected_index
        if index not in (3, 7):
            return ""
        view = self._views.get(index)
        if view is None:
            return ""
        try:
            field = view.dpd_fields.get_field("lemma_1")
            lemma_1 = (field.value or "").strip() if field else ""
            return re.sub(r" \d.*$", "", lemma_1)
        except Exception:
            return ""

    def _view(self, index: int) -> ft.Control:
        """Build (once) and return the view for a tab index."""
        with self._build_lock:
            if index not in self._views:
                self._views[index] = self._view_builders[index]()
            return self._views[index]

    def _ensure_tab_built(self, index: int) -> None:
        """Swap the real view into a tab the first time it is shown."""
        with self._build_lock:
            if index in self._mounted_tabs:
                return
            self.tabs.tabs[index].content = self._view(index)
            self._mounted_tabs.add(index)
        self.page.update()

    def _maybe_start_db_init(self) -> None:
        # started at launch; this remains as a retry path if that load failed
        if self._db_init_started or self.toolkit.db_manager.all_lemma_1 is not None:
            return
        self._db_init_started = True
        self.page.run_thread(self._initialize_db_in_background)

    def _on_tab_activated(self, e: ft.ControlEvent | None = None) -> None:
        """Build the newly-active tab's content on demand and kick db init."""
        self._ensure_tab_built(self.tabs.selected_index)
        self._maybe_start_db_init()

    def _initialize_db_in_background(self) -> None:
        try:
            self.toolkit.db_manager.initialize_db()
            show_global_snackbar(self.page, "Database loaded.", "info", 2000)
        except Exception as ex:
            self._db_init_started = False
            show_global_snackbar(
                self.page, f"Database load failed: {ex}", "error", 5000
            )

    def _warmup_in_background(self) -> None:
        """Build every tab (most-used first), then the heavy managers, so
        nothing waits on a first click. Runs alongside the db load."""
        # A failing builder leaves its tab unmounted (retried on click) and
        # must not abort the warm-up of the remaining tabs and managers.
        failed: list[str] = []
        for index in self._warmup_tab_order:
            try:
                self._ensure_tab_built(index)
            except Exception:
                failed.append(self.tabs.tabs[index].text or str(index))
        try:
            self.toolkit.wordfinder_manager
            self.toolkit.wordfinder_popup
            self.toolkit.ai_manager
            self.toolkit.bold_definitions_search_manager
        except Exception as ex:
            failed.append(str(ex))
        if failed:
            show_global_snackbar(
                self.page, f"Warm-up failed for: {', '.join(failed)}", "error", 5000
            )
        else:
            show_global_snackbar(self.page, "All tabs and tools ready.", "info", 2000)

    def build_ui(self) -> None:
        """Constructs the main UI elements."""

        # Tab order must match the _view_builders index keys. Each tab starts
        # with a lightweight placeholder; the real view is built and mounted on
        # first selection by _on_tab_activated.
        tab_labels = [
            "Global",
            "Transl",
            "Pass1Auto",
            "Pass1Add",
            "Pass2Pre",
            "Pass2x",
            "Pass2Auto",
            "Pass2Add",
            "'",
            "Sandhi",
            "DB",
            "Tests",
            "Bold Search",
            "√",
            "CT",
        ]
        self.tabs: ft.Tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_click=self._on_tab_activated,
            on_change=self._on_tab_activated,
            tabs=[
                ft.Tab(text=label, content=ft.Container(expand=True))
                for label in tab_labels
            ],
            expand=True,
        )

        # The first tab is visible at startup, so build it eagerly.
        self._mounted_tabs.add(0)
        self.tabs.tabs[0].content = self._view(0)

        self.page.add(self.tabs)
        self.page.update()

        # Window has painted — load everything else in the background:
        # the db (longest task) and the tab/manager warm-up in parallel.
        self._db_init_started = True
        self.page.run_thread(self._initialize_db_in_background)
        self.page.run_thread(self._warmup_in_background)


def main(page: ft.Page) -> None:
    # Enable/disable profiling
    enable_profiling = False
    profile_file = Path("gui2_profile.prof")

    if enable_profiling:
        profiler = cProfile.Profile()
        profiler.enable()

    # Time App initialization
    start_time = time.time()
    App(page)
    print(f"App initialized in {time.time() - start_time:.2f}s")

    # Start the FastAPI server after the UI has painted so it never delays the
    # window appearing.
    start_time = time.time()
    start_dpd_server()
    print(f"FastAPI server started in {time.time() - start_time:.2f}s")

    if enable_profiling:
        profiler.disable()
        profiler.dump_stats(str(profile_file))


if __name__ == "__main__":
    ft.app(target=main)
