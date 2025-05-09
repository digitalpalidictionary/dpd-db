import re
import flet as ft
from icecream import ic
from sqlalchemy import or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.toolkit import ToolKit
from tools.paths import ProjectPaths


class SandhiFindReplaceView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ):
        super().__init__(expand=True, spacing=5, controls=[])
        self.page = page
        self.toolkit: ToolKit = toolkit

        self.find_me: str = ""
        self.replace_me: str = ""
        self.data: Data = Data()

        # UI elements
        self.find_text = ft.TextField("", width=400)
        self.replace_text = ft.TextField("", width=400)
        self.find_button = ft.ElevatedButton("Find", on_click=self.find_clicked)
        self.clear_button = ft.ElevatedButton("Clear", on_click=self.clear_search)
        self.message = ft.Text("", expand=True)
        self.found_field = ft.Text(width=800, expand=True, selectable=True)
        self.replaced_field = ft.Text(width=800, expand=True, selectable=True)
        self.commit_button = ft.ElevatedButton("Commit", on_click=self.commit_clicked)
        self.ignore_button = ft.ElevatedButton("Ignore", on_click=self.ignore_clicked)

        # Build sections
        self._top_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Find:", width=100),
                            self.find_text,
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Replace:", width=100),
                            self.replace_text,
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Container(width=100),
                            self.find_button,
                            self.clear_button,
                        ]
                    ),
                    ft.Row([self.message]),
                ]
            ),
            padding=10,
        )

        self._middle_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(width=100),
                            self.commit_button,
                            self.ignore_button,
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Found:", width=100),
                            self.found_field,
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Replaced:", width=100),
                            self.replaced_field,
                        ]
                    ),
                ]
            ),
            padding=10,
            expand=True,
        )

        self.controls = [self._top_section, self._middle_section]

    def update_message(self, text: str):
        self.message.value = text
        self.update()

    def clear_fields(self):
        self.found_field.value = ""
        self.found_field.spans = []
        self.replaced_field.value = ""
        self.replaced_field.spans = []
        self.update()

    def clear_search(self, e):
        self.find_text.value = ""
        self.replace_text.value = ""
        self.message.value = ""
        self.found_field.value = ""
        self.replaced_field.value = ""
        self.update()

    def find_clicked(self, e):
        if self.find_text.value and self.replace_text.value:
            self.update_message("")
            self.find_me = self.find_text.value
            self.replace_me = self.replace_text.value
            self._initiate_find_replace()
        else:
            self.update_message("Please enter both find and replace values")

    def _initiate_find_replace(self):
        message = self.data.search_db(self.find_me)
        if len(self.data.db_results) > 0:
            self.update_message(message)
            self._load_next_result()
        else:
            self.update_message("No results found")
            self.clear_fields()

    def _load_next_result(self):
        if self.data.index >= len(self.data.db_results):
            self.update_message("End of results")
            self.clear_fields()
            self.data.index = 0
            return

        self.update_message(
            f"{self.data.index + 1}/{len(self.data.db_results)} {self.data.this_field_name}"
        )

        if re.findall(self.find_me, self.data.this_field_text):
            self._highlight_found(self.data.this_field_text)
            self._highlight_replaced(self.data.this_field_text)
        else:
            self._increment()

    def _increment(self):
        if self.data.column_index == 2:  # last column
            if self.data.index < len(self.data.db_results):
                self.data.column_index = 0
                self.data.index += 1
                self._load_next_result()
        else:
            self.data.column_index += 1
            self._load_next_result()

    def commit_clicked(self, e):
        new_value = re.sub(self.find_me, self.replace_me, self.data.this_field_text)
        setattr(self.data.this_headword, self.data.this_field_name, new_value)
        self.data.commit()
        self._increment()

    def ignore_clicked(self, e):
        self._increment()
        self._load_next_result()

    def _highlight_found(self, text):
        spans = []
        parts = re.split(self.find_me, text)
        for i, part in enumerate(parts):
            spans.append(ft.TextSpan(part))
            if i != len(parts) - 1:
                spans.append(
                    ft.TextSpan(
                        self.find_me,
                        style=ft.TextStyle(bgcolor=ft.Colors.BLUE),
                    )
                )
        self.found_field.spans = spans
        self.update()

    def _highlight_replaced(self, text):
        spans = []
        parts = re.split(self.find_me, text)
        for i, part in enumerate(parts):
            spans.append(ft.TextSpan(part))
            if i != len(parts) - 1:
                spans.append(
                    ft.TextSpan(
                        self.replace_me,
                        style=ft.TextStyle(bgcolor=ft.Colors.GREEN),
                    )
                )
        self.replaced_field.spans = spans
        self.update()


class Data:
    """Database manager."""

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db_results: list[DpdHeadword] = []
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

    def refresh_db_session(self):
        self.db_session.close()
        self.db_session = get_db_session(self.pth.dpd_db_path)

    def search_db(self, find_me) -> str:
        self.refresh_db_session()
        find_me_escaped = re.escape(find_me)

        self.db_results = (
            self.db_session.query(DpdHeadword)
            .filter(
                or_(
                    DpdHeadword.example_1.regexp_match(find_me_escaped),
                    DpdHeadword.example_2.regexp_match(find_me_escaped),
                    DpdHeadword.commentary.regexp_match(find_me_escaped),
                )
            )
            .all()
        )

        if len(self.db_results) > 0:
            return f"{len(self.db_results)} results found"
        return "No results found"

    def commit(self):
        try:
            self.db_session.commit()
        except Exception as e:
            print(f"Commit failed: {str(e)}")
            self.db_session.rollback()
            raise
