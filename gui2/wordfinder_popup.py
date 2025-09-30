# -*- coding: utf-8 -*-
import flet as ft

from tools.printer import printer as pr


class WordFinderPopup:
    def __init__(self, toolkit):
        from gui2.toolkit import ToolKit

        self.toolkit: ToolKit = toolkit
        self.page: ft.Page = toolkit.page
        self.wordfinder = toolkit.wordfinder_manager

        # UI elements - adapted from WordFinderWidget
        self.search_field = ft.TextField(
            label="Wordfinder",
            label_style=ft.TextStyle(color=ft.Colors.WHITE, size=10),
            width=500,
            on_submit=self._handle_search,
            border_radius=20,
            border=None,
            autofocus=True,
            bgcolor=ft.Colors.GREY_900,  # Darker field background
        )

        self.search_button = ft.ElevatedButton(
            text="Search",
            on_click=self._handle_search,
        )

        self.clear_button = ft.ElevatedButton(
            text="Clear",
            on_click=self._handle_clear,
        )

        self.search_type_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("EXACT"),
                ft.dropdown.Option("STARTS_WITH"),
                ft.dropdown.Option("CONTAINS"),
                ft.dropdown.Option("REGEX"),
            ],
            value="STARTS_WITH",  # Default
            label="Search Type",
            label_style=ft.TextStyle(color=ft.Colors.WHITE, size=10),
            width=300,
            border_radius=20,
        )

        self.results_container = ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            visible=False,
            padding=10,
            border_radius=20,
            width=1350,
            height=1000,  # Reduced to ensure it fits within screen bounds
            bgcolor=ft.Colors.GREY_900,  # Darker background for results
            border=ft.border.all(1, ft.Colors.BLUE_200),
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Word Finder", size=14, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREY_900,  # Darker background
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                self.search_field,
                                self.search_button,
                                self.clear_button,
                                self.search_type_dropdown,
                            ],
                            spacing=10,
                        ),
                        self.results_container,
                    ],
                ),
                width=1375,  # Same width as main window
                height=1280,  # Full screen height
                bgcolor=ft.Colors.GREY_900,  # Darker background for content
            ),
            actions=[
                ft.TextButton("Close", on_click=self._handle_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_search(self, e: ft.ControlEvent) -> None:
        word = (self.search_field.value or "").strip()
        search_type = self.search_type_dropdown.value
        if not word:
            self._show_error("Please enter a word to search.")
            return

        try:
            self.wordfinder.search_for(word, search_type, printer=False)
            results = self.wordfinder.format_results(self.wordfinder.search_results)
            if results:
                self.results_container.content = ft.Column(
                    [
                        ft.Text(
                            result,
                            color=ft.Colors.WHITE,
                            selectable=True,
                        )
                        for result in results
                    ],
                    scroll=ft.ScrollMode.AUTO,
                )
                self.results_container.visible = True
                self.dialog.update()
            else:
                self._show_error("No results found.")
        except Exception as ex:
            pr.error(f"Wordfinder search error in popup: {ex}")
            self._show_error(f"Search error: {str(ex)}")

    def _handle_clear(self, e: ft.ControlEvent | None) -> None:
        self.results_container.visible = False
        self.results_container.content = ft.Column(
            [],
            scroll=ft.ScrollMode.AUTO,
        )
        self.search_field.value = ""
        self.dialog.update()

    def _handle_close(self, e: ft.ControlEvent | None) -> None:
        self.dialog.open = False
        self.page.update()

    def _show_error(self, message: str) -> None:
        self.results_container.content = ft.Column(
            [
                ft.Text(
                    message,
                    color=ft.Colors.RED,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        self.results_container.visible = True
        self.dialog.update()

    def open_popup(self) -> None:
        self.search_field.value = ""
        self.results_container.visible = False
        self.results_container.content = ft.Column(
            [],
            scroll=ft.ScrollMode.AUTO,
        )
        self.page.open(self.dialog)
        self.page.update()

    def is_dialog_open(self) -> bool:
        return self.dialog.open

    def close_dialog(self) -> None:
        if self.is_dialog_open():
            self._handle_close(None)
