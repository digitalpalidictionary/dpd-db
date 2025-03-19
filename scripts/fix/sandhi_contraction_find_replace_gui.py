#!/usr/bin/env python3

"""Find and replace sandhi contractions (imam'eva) in
1. example_1
2. example_2 and
3. commentary.
"""

import re

import flet as ft
from icecream import ic
from rich import print
from sqlalchemy import func, or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


class Controller:
    def __init__(self, page):
        self.ui = Gui(self, page)
        self.data = Data()

        self.find_me: str
        self.replace_me: str

    def initiate_find_replace(self):
        message = self.data.search_db(self.find_me)
        if len(self.data.db_results) > 0:
            self.ui.update_message(message)
            self.load_next_result_into_gui()
        else:
            self.ui.update_message("no results found")
            self.ui.clear_fields()
            self.ui.page.update()

    def load_next_result_into_gui(self):
        """Find the next result and load it into gui."""
        ic(self.data.index)
        ic(self.data.column_index)

        if self.data.index >= len(self.data.db_results):
            self.ui.update_message("end of results")
            self.ui.clear_fields()
            return

        self.ui.update_message(
            f"{self.data.index + 1} / {len(self.data.db_results)} {self.data.this_field_name}"
        )

        if re.findall(self.find_me, self.data.this_field_text):
            self.ui.highlight_found(self.data.this_field_text)
            self.ui.highlight_replaced(self.data.this_field_text)
        else:
            self.increment()

    def increment(self):
        """Increment the index and column."""
        if self.data.column_index == 2:  # last column
            if self.data.index < len(self.data.db_results):
                self.data.column_index = 0
                self.data.index += 1
                self.load_next_result_into_gui()
        else:
            self.data.column_index += 1
            self.load_next_result_into_gui()

    def process_commit(self):
        new_value = re.sub(self.find_me, self.replace_me, self.data.this_field_text)

        setattr(self.data.this_headword, self.data.this_field_name, new_value)
        self.data.commit()
        self.increment()


class Gui:
    """Flet gui."""

    height = 250
    width = 1000

    def __init__(self, control: Controller, page: ft.Page):
        self.control = control
        self.page = page
        self.page.title = "Find and Replace Sandhi Contractions"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 100
        self.page.spacing = 10
        self.page.window.height = 1280

        # Set up the keyboard event handler
        self.page.on_keyboard_event = self.on_keyboard

        # Create controls
        self.find_text = ft.TextField("", width=self.width)
        self.replace_text = ft.TextField("", width=self.width)
        self.find_button = ft.ElevatedButton("find", on_click=self.find_clicked)
        self.clear_button = ft.ElevatedButton("clear", on_click=self.clear_search)
        self.message = ft.Text("", expand=True)

        self.found_field = ft.Text(width=self.width, expand=True)
        self.replaced_field = ft.Text(width=self.width, expand=True, selectable=True)

        # buttons

        self.commit_button = ft.ElevatedButton("commit", on_click=self.commit_clicked)
        self.ignore_button = ft.ElevatedButton("ignore", on_click=self.ignore_clicked)

        # Add controls to page
        self.page.add(
            ft.Row([self.label("find"), self.find_text]),
            ft.Row([self.label("replace"), self.replace_text]),
            ft.Row([self.label(""), self.find_button, self.clear_button]),
            ft.Divider(),
            ft.Row([self.label(""), self.message]),
            ft.Divider(),
            ft.Column(
                [
                    ft.Row([self.label(""), self.commit_button, self.ignore_button]),
                    ft.Row([self.label("found"), self.found_field]),
                    ft.Row([self.label("replaced"), self.replaced_field]),
                ],
                expand=True,
                expand_loose=True,
                spacing=30,
            ),
        )
        self.page.update()

    # Handle Ctrl+Q to quit
    def on_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

    def label(self, label):
        """Makes a text label."""
        return ft.Text(label, width=100)

    def update_message(self, text: str):
        """Updates the window message."""
        self.message.value = text
        self.page.update()

    def clear_fields(self):
        """Clears the bottom boxes."""
        self.found_field.value = ""
        self.found_field.spans = []
        self.replaced_field.value = ""
        self.replaced_field.spans = []
        self.page.update()

    def clear_search(self, e):
        "Clears the search fields."
        self.find_text.value = ""
        self.replace_text.value = ""
        self.message.value = ""
        self.page.update()

    def find_clicked(self, e):
        """Manage find and replace."""
        if self.find_text.value and self.replace_text.value:
            self.update_message("")
            self.control.find_me = self.find_text.value
            self.control.replace_me = self.replace_text.value
            self.control.initiate_find_replace()
            self.page.update()
        else:
            self.update_message("shooting blanks")

    def commit_clicked(self, e):
        """Handle commit button click."""
        self.control.process_commit()

    def ignore_clicked(self, e):
        """Handle ignore button click."""
        self.control.increment()
        self.control.load_next_result_into_gui()

    def highlight_found(self, text):
        """Turns paragraph of text into a list of TextSpan."""

        spans = []
        parts = re.split(self.control.find_me, text)

        for i, part in enumerate(parts):
            spans.append(ft.TextSpan(part))
            if i != len(parts) - 1:
                spans.append(
                    ft.TextSpan(
                        self.control.find_me,
                        style=ft.TextStyle(bgcolor=ft.Colors.BLUE),
                    )
                )
        self.found_field.spans = spans
        self.page.update()

    def highlight_replaced(self, text):
        """Turns paragraph into a list of spans."""

        spans = []
        parts = re.split(self.control.find_me, text)

        for i, part in enumerate(parts):
            spans.append(ft.TextSpan(part))
            if i != len(parts) - 1:
                spans.append(
                    ft.TextSpan(
                        self.control.replace_me,
                        style=ft.TextStyle(bgcolor=ft.Colors.GREEN),
                    )
                )
        self.replaced_field.spans = spans
        self.page.update()


class Data:
    """Database manager."""

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db_results: list[DpdHeadword]
        self.index: int = 0
        self.column_index: int = 0
        self.columns: list[str] = ["example_1", "example_2", "commentary"]

    @property
    def this_headword(self) -> DpdHeadword:
        return self.db_results[self.index]

    @property
    def this_field_name(self) -> str:
        return self.columns[self.column_index]

    @property
    def this_field_text(self) -> str:
        return getattr(self.this_headword, self.this_field_name)

    def search_db(self, find_me) -> str:
        # refresh the session
        self.db_session.close()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        self.db_results = (
            self.db_session.query(DpdHeadword)
            .filter(
                or_(
                    DpdHeadword.example_1.regexp_match(find_me),
                    DpdHeadword.example_2.regexp_match(find_me),
                    DpdHeadword.commentary.regexp_match(find_me),
                )
            )
            .all()
        )

        if len(self.db_results) > 0:
            return f"{len(self.db_results)} results found"

        # search within bold tags
        self.db_results = (
            self.db_session.query(DpdHeadword)
            .filter(
                or_(
                    func.replace(
                        func.replace(DpdHeadword.example_1, "<b>", ""), "</b>", ""
                    ).contains(find_me),
                    func.replace(
                        func.replace(DpdHeadword.example_2, "<b>", ""), "</b>", ""
                    ).contains(find_me),
                    func.replace(
                        func.replace(DpdHeadword.commentary, "<b>", ""), "</b>", ""
                    ).contains(find_me),
                )
            )
            .all()
        )
        if len(self.db_results) > 0:
            return "results found in <b> tags</"
        else:
            return "nothing found whatsoever"

    def commit(self):
        """Commit to db."""
        try:
            self.db_session.commit()

        except Exception as e:
            print(f"Commit failed: {str(e)}")
            self.db_session.rollback()
            print("Rollback complete")
            raise


def main(page: ft.Page):
    Controller(page)


if __name__ == "__main__":
    ft.app(target=main)

"""
What have I learned from this exercise?

MVC architecture good for managing GUI programs. 

A little verbose, but allows fine control.

First initialize Control with Data and UI inside it
Pass Control to the UI as self.

C <> Data
C <> UI
Data x UI

Don' t use for loops, use index logic to increment through the data.
Double check your increment logix!

Use split to make Flet TextSpans to highlight text.

Keep all db stuff in one place.

Use @properties to create derived data.

"""
