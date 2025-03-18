#!/usr/bin/env python3

"""Find and replace sandhi contractions (imam'eva) in
1. example_1
2. example_2 and
3. commentary.
"""

import re
import flet as ft

from sqlalchemy import or_
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.paths import ProjectPaths


class Controller:
    def __init__(self, page):
        self.ui = Gui(self, page)
        self.data = Data()

        self.find_me: str
        self.replace_me: str

        self.index = 0
        self.column_index: int = 0
        self.current_result: DpdHeadword
        self.columns: list[str] = ["example_1", "example_2", "commentary"]
        self.current_field: str

    def initiate_find_replace(self):
        self.data.search_db(self.find_me)
        self.index = 0
        self.column_index = 0
        if len(self.data.db_results) > 0:
            self.ui.update_message(f"{len(self.data.db_results)} results found")
            self.load_next_result_into_gui()
        else:
            self.ui.update_message("no results found")
            self.ui.clear_fields()
            self.ui.page.update()

    def increment(self):
        """Increment the index and column."""

        if self.column_index == 2:  # last column
            if self.index < len(self.data.db_results):
                self.column_index = 0
                self.index += 1
            else:
                self.ui.update_message("end of results")
        else:
            self.column_index += 1

    def load_next_result_into_gui(self):
        """Find the next result and load it into gui."""

        if self.index >= len(self.data.db_results):
            self.ui.update_message("end of results")
            self.ui.clear_fields()
            return

        self.ui.update_message(
            f"{self.index + 1} / {len(self.data.db_results)} {self.columns[self.column_index].replace('_', '')}"
        )
        self.current_result = self.data.db_results[self.index]
        self.current_field = getattr(
            self.current_result, self.columns[self.column_index]
        )
        if re.findall(self.find_me, self.current_field):
            self.ui.highlight_found()
            self.ui.highlight_replaced()
            self.increment()
        else:
            self.increment()
            self.load_next_result_into_gui()


class Gui:
    """Flet gui."""

    height = 150
    width = 1000

    def __init__(self, control: Controller, page: ft.Page):
        self.control = control
        self.page = page
        self.page.title = "Find and Replace Sandhi Contractions"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 100
        self.page.spacing = 10
        self.page.window.height = 1280

        # Create controls
        self.find_text = ft.TextField("", width=self.width)
        self.replace_text = ft.TextField("", width=self.width)
        self.find_button = ft.ElevatedButton("find", on_click=self.find_replace_clicked)
        self.message = ft.Text("", expand=True)

        self.found_field = ft.Column(width=self.width, height=self.height)
        self.replaced_field = ft.Column(width=self.width, height=self.height)

        # buttons

        self.commit_button = ft.ElevatedButton("commit", on_click=self.commit_clicked)
        self.ignore_button = ft.ElevatedButton("ignore", on_click=self.ignore_clicked)

        # Add controls to page
        self.page.add(
            ft.Row([self.label("find"), self.find_text]),
            ft.Row([self.label("replace"), self.replace_text]),
            ft.Row([self.label(""), self.find_button]),
            ft.Divider(),
            ft.Row([self.label(""), self.message]),
            ft.Divider(),
            ft.Row([self.label("found"), self.found_field]),
            ft.Row([self.label("replaced"), self.replaced_field]),
            ft.Row([self.label(""), self.commit_button, self.ignore_button]),
        )
        self.page.update()

    def label(self, label):
        """Makes a text label."""
        return ft.Text(label, width=100)

    def update_message(self, text: str):
        self.message.value = text
        self.page.update()

    def clear_fields(self):
        self.found_field.controls = []
        self.replaced_field.controls = []

    def find_replace_clicked(self, e):
        if self.find_text.value and self.replace_text.value:
            self.control.find_me = self.find_text.value
            self.control.replace_me = self.replace_text.value
            self.control.initiate_find_replace()
            self.page.update()

    def commit_clicked(self, e):
        print("commit clicked")
        print("logix to save goes here")
        self.control.load_next_result_into_gui()
        self.page.update()

    def ignore_clicked(self, e):
        print("ignore clicked")
        self.control.load_next_result_into_gui()
        self.page.update()

    def highlight_found(self):
        """Turns paragraph into a list of spans."""

        spans = []
        parts = re.split(self.control.find_me, self.control.current_field)

        for i, part in enumerate(parts):
            spans.append(ft.TextSpan(part))
            if i != len(parts) - 1:
                spans.append(
                    ft.TextSpan(
                        self.control.find_me,
                        style=ft.TextStyle(bgcolor=ft.Colors.BLUE),
                    )
                )
        self.found_field.controls = [
            ft.Text(spans=spans, selectable=True, width=self.width)
        ]
        self.page.update()

    def highlight_replaced(self):
        """Turns paragraph into a list of spans."""

        spans = []
        parts = re.split(self.control.find_me, self.control.current_field)

        for i, part in enumerate(parts):
            spans.append(ft.TextSpan(part))
            if i != len(parts) - 1:
                spans.append(
                    ft.TextSpan(
                        self.control.replace_me,
                        style=ft.TextStyle(bgcolor=ft.Colors.GREEN),
                    )
                )
        self.replaced_field.controls = [
            ft.Text(spans=spans, selectable=True, width=self.width)
        ]
        self.page.update()


class Data:
    """Database manager."""

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db_results: list[DpdHeadword]

    def search_db(self, find_me):
        self.db_results = (
            self.db_session.query(DpdHeadword)
            .filter(
                or_(
                    DpdHeadword.example_1.contains(find_me),
                    DpdHeadword.example_2.contains(find_me),
                    DpdHeadword.commentary.contains(find_me),
                )
            )
            .all()
        )


def main(page: ft.Page):
    Controller(page)


if __name__ == "__main__":
    ft.app(target=main)

"""
What have I learned from this exercise?

MVC architecture is not too bad for managing GUI programs. 

A little verbose.

First initialize Control with Data and UI inside it
Pass Control to the UI as self.

C <> Data
C <> UI
Data x UI

Don' t use for loops, use index logic to increment through the data.

Use split to make Flet TextSpans to highlight text.


"""
