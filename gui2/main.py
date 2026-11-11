import asyncio
import cProfile
import re
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import flet as ft

from gui2.ai_search_window import launch_ai_search_window
from gui2.contributor_tabs import allowed_tabs, resolve_extra_tabs
from gui2 import server_lifecycle
from gui2.shortcuts_dialog import ShortcutGroup, build_shortcuts_dialog
from gui2.toolkit import ToolKit
from gui2.ui_utils import cancel_top_dialog, is_dialog_open, show_global_snackbar
from tools.printer import printer as pr
from tools.server_mode import is_headless_server

if TYPE_CHECKING:
    from gui2.filter_tab_view import FilterTabView

# Tab order must match the App._view_builders index keys.
TAB_LABELS: list[str] = [
    "Global",
    "Transl",
    "Pass1Auto",
    "Pass1Add",
    "Pass2Pre",
    "Pass2x",
    "Pass2Auto",
    "Pass2Add",
    "'",
    "Sp",
    "Sandhi",
    "DB",
    "Tests",
    "Bold Search",
    "√",
    "CT",
    "Infl",
]

TAB_TOOLTIPS: dict[str, str] = {
    "Global": "Backup, inflections and Anki update.",
    "Transl": "Look up translations of Pāḷi texts.",
    "Pass1Auto": "Run the automatic first pass over a book.",
    "Pass1Add": "Add new words from a book, one at a time.",
    "Pass2Pre": "Prepare the words of a book for the second pass.",
    "Pass2x": "Work through words that occur in the commentary.",
    "Pass2Auto": "Run the automatic second pass over a book.",
    "Pass2Add": "Edit a word that is already in the dictionary.",
    "'": "Find and replace sandhi in the dictionary.",
    "Sp": "Find and replace spelling in the dictionary.",
    "Sandhi": "Check sandhi splits of words.",
    "DB": "Search and filter the dictionary.",
    "Tests": "Run the dictionary's internal tests.",
    "Bold Search": "Search the bold definitions in the commentaries.",
    "√": "Browse the verbal roots.",
    "CT": "Manage the compound type rules, and search the words by type.",
    "Infl": "Browse the inflection tables.",
}


def tab_tooltip(label: str, shortcut: str | None, show_key: bool) -> str:
    """A tab's hover text: its description, then its Alt key if it has one."""
    text = TAB_TOOLTIPS[label]
    if shortcut and show_key:
        text = f"{text} Alt+{shortcut}"
    return text


def tab_selection() -> tuple[list[int], frozenset[int]]:
    """The tab indices to show and the read-only ones. A contributor-server
    session gets its allowed tabs; every other role gets all of them."""
    if not is_headless_server():
        return list(range(len(TAB_LABELS))), frozenset()
    visible, read_only = allowed_tabs(TAB_LABELS, resolve_extra_tabs())
    return visible, frozenset(read_only)


class App:
    # Tab-bar position -> tab index. Every index-based lookup below keeps the
    # 17 original indices; only the tab bar and its bodies use positions. The
    # desktop shows every tab, so this is the identity list there.
    _visible: list[int] = list(range(len(TAB_LABELS)))
    _read_only: frozenset[int] = frozenset()

    # Most-used tabs first so they are ready soonest.
    _WARMUP_TAB_ORDER: tuple[int, ...] = (
        7,
        4,
        5,
        6,
        2,
        3,
        1,
        13,
        11,
        8,
        9,
        10,
        12,
        14,
        15,
    )

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._db_init_started: bool = False
        self._warmup_started: bool = False
        # Guards _views/_mounted_tabs: the warm-up worker builds tabs in the
        # background while the user may click one on the UI thread.
        self._build_lock = threading.RLock()
        # Constructed here rather than in build_ui so the background db load,
        # which toggles it, cannot outrace its creation.
        self._loading_bar = ft.ProgressBar(visible=False)

        page.theme = ft.Theme()
        page.theme.font_family = "Inter"
        # Stated rather than inherited from the system, which is what the other
        # three Flet apps in this repo do. The editor's colours — including the
        # field border constant in ui_utils — were all chosen against a dark
        # ground, so following a light system theme would render them wrong.
        page.theme_mode = ft.ThemeMode.DARK
        # No window title by the user's choice. The taskbar name and icon do not
        # come from here anyway — on Linux they come from the desktop entry whose
        # `StartupWMClass` matches the Flutter client's WM_CLASS, and
        # `window.icon` is Windows-only and wants a `.ico`.
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
        # Desktop (legacy) contributors get the git-based Submit/Update buttons.
        # Server contributors do not: sync is automated (role contributor-server).
        if (
            self.toolkit.username_manager.is_not_primary()
            and not self.toolkit.username_manager.is_server_contributor()
        ):
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

        if page.web:
            # A page-level AppBar is fixed, and on a short tablet screen it and
            # the tab row leave no room for the fields. This header sits in the
            # scrolling canvas instead, so it scrolls away.
            self.toolkit.appbar_updater.counter = cast(ft.Text, appbar_actions[0])
            self._web_header = ft.Container(
                content=ft.Row(
                    [ft.Text("dpd gui", size=22), ft.Row(appbar_actions)],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=ft.Colors.LIGHT_BLUE_900,
                padding=ft.Padding.symmetric(horizontal=20),
                height=56,
            )
        else:
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
        # Pass1Auto view's controller. Where the Pass1Auto tab is hidden,
        # Pass1Add gets a controller with no view (see _make_pass1_add).
        self._views: dict[int, ft.Control] = {}
        self._mounted_tabs: set[int] = set()
        self._visible, self._read_only = tab_selection()
        # The server opens on Pass1Add, never on a safe tab that sorts before
        # it; the desktop opens on its first tab, Global.
        self._start_index: int = 3 if is_headless_server() else self._visible[0]
        self._focused_tab_index: int = self._start_index
        self._view_builders: dict[int, Callable[[], ft.Control]] = {
            0: self._make_global,
            1: self._make_translations,
            2: self._make_pass1_auto,
            3: self._make_pass1_add,
            4: self._make_pass2_pre,
            5: self._make_pass2x_in_commentary,
            6: self._make_pass2_auto,
            7: self._make_pass2_add,
            8: self._make_sandhi_find_replace,
            9: self._make_spelling_find_replace,
            10: self._make_sandhi,
            11: self._make_filter_tab,
            12: self._make_tests,
            13: self._make_bold_search,
            14: self._make_roots,
            15: self._make_compound_type,
            16: self._make_inflection_templates,
        }

        self.build_ui()

        self.toolkit.username_manager.get_username()

    def _make_global(self) -> ft.Control:
        from gui2.global_tab_view import GlobalTabView

        return GlobalTabView(self.page, self.toolkit)

    def _make_translations(self) -> ft.Control:
        from gui2.translations_view import TranslationsView

        return TranslationsView(self.page, self.toolkit)

    def _make_pass1_auto(self) -> ft.Control:
        from gui2.pass1_auto_view import Pass1AutoView

        return Pass1AutoView(self.page, self.toolkit)

    def _make_pass1_add(self) -> ft.Control:
        from gui2.pass1_add_view import Pass1AddView

        if 2 in self._visible:
            controller = self._view(2).controller  # the Pass1Auto view's own
        else:
            # Pass1Add reads only this controller's word lists. Building the
            # hidden Pass1Auto view for it would build every AI client, which
            # nothing on a contributor's page can use.
            from gui2.pass1_auto_controller import Pass1AutoController

            controller = Pass1AutoController(None, self.toolkit)
        return Pass1AddView(self.page, self.toolkit, controller)

    def _make_pass2_pre(self) -> ft.Control:
        from gui2.pass2_pre_view import Pass2PreProcessView

        return Pass2PreProcessView(self.page, self.toolkit)

    def _make_pass2x_in_commentary(self) -> ft.Control:
        from gui2.pass2x.in_commentary_view import Pass2xInCommentaryView

        return Pass2xInCommentaryView(self.page, self.toolkit)

    def _make_pass2_auto(self) -> ft.Control:
        from gui2.pass2_auto_view import Pass2AutoView

        return Pass2AutoView(self.page, self.toolkit)

    def _make_pass2_add(self) -> ft.Control:
        from gui2.pass2_add_view import Pass2AddView

        return Pass2AddView(self.page, self.toolkit)

    def _make_sandhi_find_replace(self) -> ft.Control:
        from gui2.sandhi_find_replace_view import SandhiFindReplaceView

        return SandhiFindReplaceView(self.page, self.toolkit)

    def _make_spelling_find_replace(self) -> ft.Control:
        from gui2.spelling_find_replace_view import SpellingFindReplaceView

        return SpellingFindReplaceView(self.page, self.toolkit)

    def _make_sandhi(self) -> ft.Control:
        from gui2.sandhi_view import SandhiView

        return SandhiView(self.page, self.toolkit)

    def release_memory(self) -> None:
        """Empty this app's data once a newer page has replaced its page."""
        with self._build_lock:
            self._views.clear()
            self._view_builders = {}
        with self.toolkit._lazy_lock:
            self.toolkit._lazy_cache.clear()
        self.toolkit.db_manager.release_memory()

    def _make_filter_tab(self) -> "FilterTabView":
        from gui2.filter_tab_view import (
            CONTRIBUTOR_DATA_FILTERS,
            CONTRIBUTOR_DISPLAY_FILTERS,
            FilterTabView,
        )

        if self.toolkit.username_manager.is_not_primary():
            return FilterTabView(
                self.page,
                self.toolkit,
                data_filters=CONTRIBUTOR_DATA_FILTERS,
                display_filters=CONTRIBUTOR_DISPLAY_FILTERS,
            )
        return FilterTabView(self.page, self.toolkit)

    def _make_tests(self) -> ft.Control:
        from gui2.tests_tab_view import TestsTabView

        return TestsTabView(self.page, self.toolkit)

    def _make_bold_search(self) -> ft.Control:
        from gui2.bold_search_view import BoldSearchView

        return BoldSearchView(self.page, self.toolkit)

    def _make_roots(self) -> ft.Control:
        from gui2.roots_tab_view import RootsTabView

        return RootsTabView(self.page, self.toolkit)

    def _make_compound_type(self) -> ft.Control:
        from gui2.compound_type_tab_view import CompoundTypeTabView

        return CompoundTypeTabView(self.page, self.toolkit)

    def _make_inflection_templates(self) -> ft.Control:
        from gui2.inflection_templates_tab_view import InflectionTemplatesTabView

        return InflectionTemplatesTabView(self.page, self.toolkit)

    def _on_submit_data(self, e: ft.ControlEvent) -> None:
        """Handle Submit Data button click."""
        from scripts.onboarding.data_submission import submit_data

        result = submit_data(Path.cwd())
        dialog = ft.AlertDialog(
            title=ft.Text("Submit Data"),
            content=ft.Text(result.message),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.page.pop_dialog()),
            ],
        )
        self.page.show_dialog(dialog)

    def _on_check_updates(self, e: ft.ControlEvent) -> None:
        """Handle Update button click with confirmation."""

        def _run_update(e: ft.ControlEvent) -> None:
            self.page.pop_dialog()
            from scripts.onboarding.contributor_update import update_environment

            summary = update_environment(Path.cwd())
            result_dialog = ft.AlertDialog(
                title=ft.Text("Update Complete"),
                content=ft.Text(summary),
                actions=[
                    ft.TextButton("OK", on_click=lambda _: self.page.pop_dialog()),
                ],
            )
            self.page.show_dialog(result_dialog)

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
                    on_click=lambda _: self.page.pop_dialog(),
                ),
                ft.TextButton(
                    "Update",
                    on_click=_run_update,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(confirm_dialog)

    # Alt+<key> jumps straight to a tab, by its index in tab_labels.
    _TAB_JUMP_KEYS: dict[str, int] = {
        "G": 0,  # Global
        "T": 1,  # Transl
        "P": 4,  # Pass2Pre
        "E": 7,  # Pass2Add
        "'": 8,  # '
        "S": 9,  # Sp
        "D": 11,  # DB
        "B": 13,  # Bold Search
        "R": 14,  # √ (Roots)
        "C": 15,  # CT (Compound Type)
        "I": 16,  # Infl
    }

    # Page scroll keys -> scroll delta in px. Numpad 9/3 are the keypad
    # PageUp/PageDown keys reported when Num Lock is off.
    _SCROLL_KEYS: dict[str, int] = {
        "Page Up": -500,
        "Page Down": 500,
        "Numpad 9": -500,
        "Numpad 3": 500,
    }

    # Alt+X runs the open tab's Clear / Clear All button handler, so the key
    # and the button can never do different things. Tabs without such a
    # button are absent and ignore the key.
    _CLEAR_ACTIONS: dict[int, Callable[[Any], None]] = {
        1: lambda view: view.clear_clicked(None),  # Transl
        2: lambda view: view.handle_clear_click(None),  # Pass1Auto
        3: lambda view: view.clear_all_fields(None),  # Pass1Add
        6: lambda view: view.handle_clear_click(None),  # Pass2Auto
        7: lambda view: view._click_clear_all(None),  # Pass2Add
        8: lambda view: view.clear_search(None),  # '
        9: lambda view: view.clear_search(None),  # Sp
        11: lambda view: view._clear_filters_clicked(None),  # DB
        13: lambda view: view.controller.clear_fields(None),  # Bold Search
        14: lambda view: view._clear_all(None),  # √ (Roots)
        15: lambda view: view._on_clear(None),  # CT (Compound Type)
        16: lambda view: view._clear_all(None),  # Infl
    }

    # Alt+? opens the shortcuts popup. Some keyboard layouts report the key
    # under "?" as "/", so both are accepted.
    _SHORTCUTS_KEYS: tuple[str, ...] = ("?", "/")

    async def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        # Some Alt keys clash with the browser's own, so they are off in the web.
        alt = e.alt and not self.page.web
        if e.key == "Q" and e.ctrl:
            await self.page.window.close()
        elif e.key == "Escape":
            await cancel_top_dialog(self.page)
        elif e.key == "A" and e.ctrl and e.shift:
            launch_ai_search_window()
        elif e.key == "F" and e.ctrl and 7 in self._visible:
            # 7 = Pass2Add: the tab the word finder is for. Without it the
            # finder is never built and the key stays dead — on Pass1Add the
            # lemma fill goes with it, deliberately.
            self.toolkit.wordfinder_popup.open_popup(self._get_current_lemma())
        elif e.key == "W" and e.ctrl and 7 in self._visible:
            # Universal close key - close any open dialog
            if self.toolkit.wordfinder_popup.is_dialog_open():
                self.toolkit.wordfinder_popup.close_dialog()
        elif e.key == "S" and e.ctrl:
            # A popup stops the mouse reaching the tab behind it, so it stops
            # the save and clear keys too.
            if is_dialog_open(self.page):
                return
            # Sourced from _views, not from the tab control: 1.0's Tab has no
            # content slot, and the hasattr checks below would simply miss,
            # so a wrong lookup here stops Ctrl+S saving without any error.
            view = self._views.get(self._current_index())
            # Ctrl+S saves in tabs that support it.
            # The first four targets are synchronous today. If any is ever made
            # `async def`, these calls become discarded coroutines and Ctrl+S
            # stops saving with no error at all — the same silent failure this
            # path already had once. Await them if that day comes.
            if hasattr(view, "_on_save_changes"):
                view._on_save_changes(None)
            elif hasattr(view, "_save_changes_clicked"):
                view._save_changes_clicked(None)
            elif hasattr(view, "_save_root"):
                view._save_root(None)
            elif hasattr(view, "_save_template"):
                view._save_template(None)
            elif hasattr(view, "commit_clicked"):
                view.commit_clicked(None)
            elif hasattr(view, "test_and_add_to_db"):
                await view.test_and_add_to_db()
            elif hasattr(view, "_click_backup_quit"):
                await view._click_backup_quit(None)
        elif e.key == "Arrow Left" and alt:
            if self.tabs.selected_index > 0:
                self.tabs.selected_index -= 1
                await self._on_tab_activated()
                self.page.update()
        elif e.key == "Arrow Right" and alt:
            if self.tabs.selected_index < len(self._tab_bar.tabs) - 1:
                self.tabs.selected_index += 1
                await self._on_tab_activated()
                self.page.update()
        elif e.key == "X" and alt:
            clear = self._CLEAR_ACTIONS.get(self._current_index())
            view = self._views.get(self._current_index())
            if clear is not None and view is not None and not is_dialog_open(self.page):
                clear(view)
        elif alt and e.key in self._SHORTCUTS_KEYS:
            if not is_dialog_open(self.page):
                self.page.show_dialog(
                    build_shortcuts_dialog(
                        self._shortcut_groups(), lambda _: self.page.pop_dialog()
                    )
                )
        elif (
            alt
            and e.key in self._TAB_JUMP_KEYS
            and self._TAB_JUMP_KEYS[e.key] in self._visible
        ):
            self.tabs.selected_index = self._visible.index(self._TAB_JUMP_KEYS[e.key])
            await self._on_tab_activated()
            self.page.update()
        elif e.key in self._SCROLL_KEYS:
            # Flet's global key handler intercepts these before any focused
            # scrollable, so page scrolling has to be driven manually. Only
            # views exposing a `_middle_section` scrollable respond (Pass2Add
            # today); others simply ignore it. "Numpad 9"/"Numpad 3" are the
            # keypad PageUp/PageDown keys reported when Num Lock is off.
            view = self._views.get(self._current_index())
            target = getattr(view, "_middle_section", None)
            if target is not None:
                await target.scroll_to(delta=self._SCROLL_KEYS[e.key], duration=100)

    def _shortcut_groups(self) -> list[ShortcutGroup]:
        """Every shortcut on_keyboard handles, for the Alt+? popup. The tab
        jumps and the Alt+X tabs come from the tables the keys act on."""
        tab_jumps = sorted(
            (
                (key, index)
                for key, index in self._TAB_JUMP_KEYS.items()
                if index in self._visible
            ),
            key=lambda item: item[1],
        )
        clear_tabs = ", ".join(
            self._tab_label(i) for i in self._CLEAR_ACTIONS if i in self._visible
        )
        # The word finder is Pass2Add's tool: without the tab, its keys do
        # nothing, so their rows are left out.
        wordfinder_open = (
            [
                ("Ctrl+F", "Open the word finder (with the lemma on the add tabs)"),
            ]
            if 7 in self._visible
            else []
        )
        wordfinder_close = (
            [("Ctrl+W", "Close the word finder")] if 7 in self._visible else []
        )
        return [
            (
                "App",
                [
                    ("Alt+?", "Show this list of shortcuts"),
                    *wordfinder_open,
                    ("Ctrl+Shift+A", "Open the AI search window"),
                    ("Ctrl+Q", "Quit the editor"),
                ],
            ),
            (
                "Tabs",
                [
                    ("Alt+←", "Go to the previous tab"),
                    ("Alt+→", "Go to the next tab"),
                    *(
                        (f"Alt+{key}", f"Go to {self._tab_label(index)}")
                        for key, index in tab_jumps
                    ),
                ],
            ),
            (
                "Save and clear (the open tab)",
                [
                    (
                        "Ctrl+S",
                        "Pass1Add, Pass2Add: run the tests, then add to the db if all pass",
                    ),
                    ("Ctrl+S", "', Sp: commit"),
                    ("Ctrl+S", "DB, CT: save changes"),
                    ("Ctrl+S", "√: save to the db"),
                    ("Ctrl+S", "Infl: save the template"),
                    ("Ctrl+S", "Global: back up the db and quit"),
                    ("Alt+X", f"Clear or Clear All on {clear_tabs}"),
                    ("Page Up / Page Down", "Scroll Pass2Add"),
                ],
            ),
            (
                "Popups",
                [
                    ("Escape", "Cancel or close the top popup"),
                    *wordfinder_close,
                    ("", "Ctrl+S and Alt+X do nothing while a popup is open"),
                ],
            ),
            (
                "AI search window",
                [("Ctrl+W or Escape", "Close the window")],
            ),
        ]

    def _get_current_lemma(self) -> str:
        """Return lemma_clean from the active add-view, or empty string."""
        index = self._current_index()
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

    def _current_index(self) -> int:
        """The tab index of the open tab (the selection is a tab-bar position)."""
        return self._visible[self.tabs.selected_index]

    def _view(self, index: int) -> ft.Control:
        """Build (once) and return the view for a tab index."""
        with self._build_lock:
            if index not in self._views:
                view = self._view_builders[index]()
                if index in self._read_only:
                    setattr(view, "read_only", True)
                    save_button = getattr(view, "save_button", None)
                    if save_button is not None:
                        save_button.disabled = True
                self._views[index] = view
            return self._views[index]

    def _ensure_tab_built(self, index: int) -> None:
        """Swap the real view into a tab the first time it is shown."""
        with self._build_lock:
            if index in self._mounted_tabs:
                return
            self._tab_bodies.controls[self._visible.index(index)] = self._view(index)
            self._mounted_tabs.add(index)
        self.page.update()

    def _maybe_start_db_init(self) -> None:
        # started at launch; this remains as a retry path if that load failed
        # Lock covers both flags' check-and-set: handlers run in a thread
        # pool, so two near-simultaneous tab clicks could otherwise each
        # reserve a worker.
        with self._build_lock:
            if self._db_init_started or self.toolkit.db_manager.all_lemma_1 is not None:
                return
            self._db_init_started = True
            self.page.run_thread(self._initialize_db_in_background)

    async def _on_tab_activated(self, e: ft.ControlEvent | None = None) -> None:
        """Build the newly-active tab's content on demand and kick db init."""
        index = self._current_index()
        if index not in self._mounted_tabs:
            # Hand the loop a turn so the placeholder spinner reaches the
            # client before the build blocks, then build off the event loop.
            # Without both halves the ring is queued and painted only after the
            # view it was meant to cover has already appeared.
            self.page.update()
            await asyncio.sleep(0)
            await asyncio.to_thread(self._ensure_tab_built, index)
        self._maybe_start_db_init()

        # Only the first call for a given tab dispatches focus. In 0.28 the
        # duplicate came from on_click and on_change both being bound; 1.0 has
        # only on_change, but the keyboard jumps still call this directly as
        # well as tripping on_change. The page.update() flushes the new
        # selected_index to the client before the view asks for focus —
        # otherwise the target field is not built yet and the request is lost.
        if index == self._focused_tab_index:
            return
        self._focused_tab_index = index
        self.page.update()
        on_tab_focus = getattr(self._views.get(index), "on_tab_focus", None)
        if on_tab_focus is not None:
            on_tab_focus()

    def _set_loading(self, loading: bool) -> None:
        """Show or hide the indeterminate bar under the app bar."""
        self._loading_bar.visible = loading
        self.page.update()

    def _initialize_db_in_background(self) -> None:
        # The longest operation in the app — ~11 s, measured — and until now it
        # ran with nothing on screen to say so.
        if getattr(self.toolkit.db_manager, "_released", None) is True:
            # A takeover emptied this app while it was starting up.
            return
        self._set_loading(True)
        try:
            self.toolkit.db_manager.initialize_db()
            show_global_snackbar(self.page, "Database loaded.", "info", 2000)
        except Exception as ex:
            # Same lock as the check-and-set in _maybe_start_db_init: a
            # failing retry's reset must not race a concurrent tab click's
            # re-reservation.
            with self._build_lock:
                self._db_init_started = False
            show_global_snackbar(
                self.page, f"Database load failed: {ex}", "error", 5000
            )
        finally:
            self._set_loading(False)
            # Serialised, not merged: the database is a prerequisite for
            # editing anything, the warm-up is speculative prefetch, and both
            # are CPU-bound so under the GIL they interleave rather than
            # parallelise. Starting the warm-up here gives the load the
            # interpreter to itself first; `finally` keeps the warm-up running
            # even when the load failed. The lock-guarded check-and-set keeps
            # a retry after a failed load from running the warm-up twice.
            with self._build_lock:
                if not self._warmup_started:
                    self._warmup_started = True
                    self.page.run_thread(self._warmup_in_background)

    def _warmup_in_background(self) -> None:
        """Build every tab (most-used first), then the heavy managers, so
        nothing waits on a first click. Started after the db load finishes."""
        if getattr(self.toolkit.db_manager, "_released", None) is True:
            # A takeover emptied this app; do not build into it.
            return
        # A failing builder leaves its tab unmounted (retried on click) and
        # must not abort the warm-up of the remaining tabs and managers.
        failed: list[str] = []
        for index in self._WARMUP_TAB_ORDER:
            if index not in self._visible:
                continue
            try:
                self._ensure_tab_built(index)
            except Exception:
                failed.append(self._tab_label(index))
        if getattr(self.toolkit.db_manager, "_released", None) is True:
            # The takeover landed while tabs were being built: the managers
            # below would reload the corpus into the freed memory.
            return
        try:
            # The word finder is Pass2Add's tool: without the tab nothing
            # can open it, so building it would just cost its ~160 MB.
            if 7 in self._visible:
                self.toolkit.wordfinder_manager
                self.toolkit.wordfinder_popup
            # Only the two Auto tabs send AI requests.
            if 2 in self._visible or 6 in self._visible:
                self.toolkit.ai_manager
            self.toolkit.bold_definitions_search_manager
            # Pre-build the synonym/phonetic detector (~0.8-0.9 s corpus
            # scan) so initialize_db can skip it and the first synonym
            # click doesn't pay for it either.
            self.toolkit.db_manager.get_relationship_detector()
        except Exception as ex:
            failed.append(str(ex))
        if failed:
            show_global_snackbar(
                self.page, f"Warm-up failed for: {', '.join(failed)}", "error", 5000
            )
        else:
            show_global_snackbar(self.page, "All tabs and tools ready.", "info", 2000)
            if self.page.web and is_headless_server():
                elapsed = time.monotonic() - server_lifecycle.PROCESS_START
                server_lifecycle.log(
                    f"tabs ready after {elapsed:.1f}s since process start"
                )

    def _tab_label(self, index: int) -> str:
        """Return a tab's visible label, for messages about that tab."""
        label = self._tab_bar.tabs[self._visible.index(index)].label
        text = getattr(label, "value", None)
        return text or str(index)

    # The editor is laid out for a desktop window. A canvas at least this tall
    # keeps its fields reachable on a short screen: the page scrolls
    # vertically instead of squeezing the fields into what the header leaves.
    _WEB_CANVAS_MIN_HEIGHT: int = 800

    def _add_web_canvas(self) -> None:
        """Put the header and the tabs on a vertically scrolling canvas."""
        self._web_canvas = ft.Container(
            content=ft.Column([self._web_header, self.tabs], spacing=0, expand=True),
            height=self._WEB_CANVAS_MIN_HEIGHT,
        )

        def fit_canvas(e: ft.PageResizeEvent) -> None:
            self._web_canvas.height = max(e.height, self._WEB_CANVAS_MIN_HEIGHT)
            self._web_canvas.update()

        self.page.on_resize = fit_canvas
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.padding = 0
        self.page.add(self._web_canvas)

    def build_ui(self) -> None:
        """Constructs the main UI elements."""

        # Each tab starts with a lightweight placeholder; the real view is
        # built and mounted on first selection by _on_tab_activated.
        tab_labels = [TAB_LABELS[index] for index in self._visible]
        # Derived from _TAB_JUMP_KEYS so the tooltips can never drift from the
        # keys the handler actually acts on.
        shortcuts = {index: key for key, index in self._TAB_JUMP_KEYS.items()}
        # In Flet 1.0 the headers and the bodies are separate controls: the
        # labels live in TabBar.tabs and the bodies in TabBarView.controls,
        # indexed in parallel. Tab itself no longer holds any content, so the
        # lazy-build mount point is the TabBarView list, not the Tab.
        self._tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(
                    label=ft.Text(
                        label,
                        tooltip=tab_tooltip(
                            label, shortcuts.get(index), not self.page.web
                        ),
                    ),
                )
                for index, label in zip(self._visible, tab_labels)
            ],
        )
        # A spinner, not an empty box: building a view takes ~1.6 s on first
        # selection and the placeholder is what the user looks at meanwhile.
        self._tab_bodies = ft.TabBarView(
            controls=[
                ft.Container(
                    content=ft.Row(
                        [ft.ProgressRing()],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
                for _ in tab_labels
            ],
            expand=True,
        )
        self.tabs: ft.Tabs = ft.Tabs(
            content=ft.Column(
                [self._loading_bar, self._tab_bar, self._tab_bodies], expand=True
            ),
            length=len(tab_labels),
            selected_index=self._visible.index(self._start_index),
            animation_duration=300,
            on_change=self._on_tab_activated,
            expand=True,
        )

        # The first tab is visible at startup, so build it eagerly.
        self._mounted_tabs.add(self._start_index)
        self._tab_bodies.controls[self._visible.index(self._start_index)] = self._view(
            self._start_index
        )

        if self.page.web:
            self._add_web_canvas()
        else:
            self.page.add(self.tabs)
        self.page.update()

        # Window has painted — load the database in the background. The
        # warm-up is not started here; it is chained from
        # _initialize_db_in_background so the two do not compete.
        self._db_init_started = True
        self.page.run_thread(self._initialize_db_in_background)


# One live app per process. A second browser tab would build a second copy of
# the app (about 560 MB measured, 2026-11-02) that holds the same contributor
# JSON in memory, and two copies rewriting one file lose each other's saves.
# The newest page wins: Flet does not always fire on_disconnect when a tab
# reloads (its send loop raises on a closing socket and skips the disconnect
# step), so waiting for the old page to say it left would lock a reloading
# contributor out.
_session_lock = threading.Lock()
_session_page: ft.Page | None = None
# The app built for the live page, so a takeover can empty it (server only).
_session_app: "App | None" = None

ALREADY_OPEN_MESSAGE = "This app is already open in another tab or window."


def claim_session(page: ft.Page) -> None:
    """Take the process's one session. The page that held it, if any, is retired."""
    global _session_page, _session_app
    with _session_lock:
        previous = _session_page
        _session_page = page
        previous_app = _session_app
        _session_app = None
    if previous is not None and previous is not page:
        try:
            # The old App stays alive in memory; without this its Ctrl+S would
            # still save from a stale copy of the contributor's file.
            previous.on_keyboard_event = None
            previous.controls.clear()
            previous.add(ft.Text(ALREADY_OPEN_MESSAGE))
        except Exception as e:
            # The old connection may already be dead; nothing is left to show.
            pr.red(f"could not retire the old page: {e}")
        try:
            from gui2.preview import retire_page

            retire_page(previous)
            # A modal left open on the old page still has working buttons.
            for dialog in list(previous._dialogs.controls):
                dialog.open = False
            previous.update()
        except Exception as e:
            pr.red(f"could not close the old page's dialogs: {e}")
    if previous_app is not None and is_headless_server():
        try:
            # Each open copy holds its own corpus and lookup sets; emptying
            # the old one first lets the new app reuse that memory. Outside
            # the retirement guard: after a disconnect _session_page is None
            # but the old app is still held, and it must be released too.
            previous_app.release_memory()
        except Exception as e:
            pr.red(f"could not release the old app: {e}")


def release_session(page: ft.Page) -> None:
    """Free the session, but only if this page is the one that holds it."""
    global _session_page
    with _session_lock:
        if _session_page is page:
            _session_page = None
    # Also on a clean close, not just a takeover: a dead page must not hold
    # the preview latch (nor its dialog graph) for the life of the process.
    try:
        from gui2.preview import retire_page

        retire_page(page)
    except Exception as e:
        pr.red(f"could not retire the closing page's preview: {e}")


def main(page: ft.Page) -> None:
    global _session_app
    # Enable/disable profiling
    enable_profiling = False
    profile_file = Path("gui2_profile.prof")

    if enable_profiling:
        profiler = cProfile.Profile()
        profiler.enable()

    # Set empty rather than left unset: an unset title is None, which the
    # desktop client fills with its own name ("flet") instead of leaving the
    # title bar blank.
    page.title = ""

    claim_session(page)
    page.on_disconnect = lambda _: release_session(page)
    page.on_close = lambda _: release_session(page)
    if page.web and is_headless_server():
        server_lifecycle.attach(page)

    # Time App initialization
    start_time = time.time()
    app = App(page)
    with _session_lock:
        # Only if this page still holds the session: a third page may have
        # taken over while the app was being built.
        if _session_page is page:
            _session_app = app
            replaced = False
        else:
            replaced = True
    if replaced and is_headless_server():
        try:
            # Nobody will ever register this app; empty it instead of leaking.
            app.release_memory()
        except Exception as e:
            pr.red(f"could not release the replaced app: {e}")
    print(f"App initialized in {time.time() - start_time:.2f}s")
    if page.web and is_headless_server():
        elapsed = time.monotonic() - server_lifecycle.PROCESS_START
        server_lifecycle.log(f"app built {elapsed:.1f}s after process start")

    if enable_profiling:
        profiler.disable()
        profiler.dump_stats(str(profile_file))


def run_app() -> None:
    from gui2.preview import PREVIEW_DIR

    # Flet looks for the assets folder once, at start, and drops it if it is
    # missing; the preview page is only written later.
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    ft.run(main)


if __name__ == "__main__":
    run_app()
