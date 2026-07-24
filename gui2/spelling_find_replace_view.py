import re

import flet as ft
from sqlalchemy import or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.toolkit import ToolKit
from tools.paths import ProjectPaths


class SpellingFindReplaceView(ft.Column):
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
        self.find_text = ft.TextField(
            "",
            width=400,
            on_blur=self.handle_find_blur,
            border_radius=20,
            border=ft.InputBorder.OUTLINE,
        )
        self.replace_text = ft.TextField(
            "",
            width=400,
            border_radius=20,
            border=ft.InputBorder.OUTLINE,
        )
        self.strip_switch = ft.Switch(label="strip", value=True)
        self.find_button = ft.ElevatedButton("Find", on_click=self.find_clicked)
        self.clear_button = ft.ElevatedButton("Clear", on_click=self.clear_search)
        self.message = ft.Text("", expand=True)
        self.found_field = ft.Text(width=800, expand=True, selectable=True)
        self.replaced_field = ft.Text(width=800, expand=True, selectable=True)
        self.commit_button = ft.ElevatedButton("Commit", on_click=self.commit_clicked)
        self.ignore_button = ft.ElevatedButton("Ignore", on_click=self.ignore_clicked)

        self._top_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Find:", width=100),
                            self.find_text,
                            self.strip_switch,
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

    def update_message(self, text: str) -> None:
        self.message.value = text
        self.update()

    def _reset_state(self) -> None:
        self.data.reset_state()

    def clear_fields(self) -> None:
        self.found_field.value = ""
        self.found_field.spans = []
        self.replaced_field.value = ""
        self.replaced_field.spans = []
        self.update()

    def clear_search(self, e: ft.ControlEvent) -> None:
        """Clear all fields, highlights, search variables and state."""
        self.find_text.value = ""
        self.replace_text.value = ""
        self.message.value = ""
        self.find_me = ""
        self.replace_me = ""
        self.clear_fields()
        self._reset_state()
        self.update()

    def find_clicked(self, e: ft.ControlEvent) -> None:
        if self.strip_switch.value:
            self.find_text.value = (self.find_text.value or "").strip()
            self.replace_text.value = (self.replace_text.value or "").strip()
            self.update()

        find_value = self.find_text.value or ""
        if not find_value:
            self.update_message("Please enter a find value")
            return

        try:
            re.compile(find_value)
        except re.error as ex:
            self.update_message(f"Invalid regex: {ex}")
            return

        self.update_message("")
        self.find_me = find_value
        self.replace_me = self.replace_text.value or ""
        self._reset_state()
        self._initiate_find_replace()

    def _initiate_find_replace(self) -> None:
        message = self.data.search_db(self.find_me)
        if len(self.data.db_results) > 0:
            self.update_message(message)
            self._load_next_result()
        else:
            self.update_message("No results found")
            self.clear_fields()

    def _load_next_result(self) -> None:
        if self.data.index >= len(self.data.db_results):
            self.update_message("End of results")
            self.clear_fields()
            self._reset_state()
            return

        text = self.data.this_field_text
        if re.search(self.find_me, text):
            headword = self.data.this_headword
            self.update_message(
                f"{self.data.index + 1}/{len(self.data.db_results)} "
                f"{headword.lemma_1} ({headword.id}) {self.data.this_field_name}"
            )
            self._highlight_found(text)
            self._highlight_replaced(text)
        else:
            self._increment()

    def _increment(self) -> None:
        self.data.increment()
        self._load_next_result()

    def commit_clicked(self, e: ft.ControlEvent) -> None:
        if not self.data.db_results or self.data.index >= len(self.data.db_results):
            self.update_message("No valid result to commit")
            return

        new_value = re.sub(self.find_me, self.replace_me, self.data.this_field_text)
        setattr(self.data.this_headword, self.data.this_field_name, new_value)
        self.data.commit()
        self.toolkit.db_manager.mark_corpus_stale()
        self._increment()

    def ignore_clicked(self, e: ft.ControlEvent) -> None:
        if not self.data.db_results or self.data.index >= len(self.data.db_results):
            self.update_message("No valid result to ignore")
            return

        self._increment()

    def handle_find_blur(self, e: ft.ControlEvent) -> None:
        """Strip the find text, copy it to replace, and focus the replace field."""
        if self.strip_switch.value and self.find_text.value:
            self.find_text.value = self.find_text.value.strip()
        if self.find_text.value and not self.replace_text.value:
            self.replace_text.value = self.find_text.value
        self.update()
        if self.strip_switch.value and self.find_text.value:
            self.replace_text.focus()

    def _highlight_found(self, text: str) -> None:
        spans: list[ft.TextSpan] = []
        last = 0
        for m in re.finditer(self.find_me, text):
            spans.append(ft.TextSpan(text[last : m.start()]))
            spans.append(
                ft.TextSpan(m.group(0), style=ft.TextStyle(bgcolor=ft.Colors.BLUE))
            )
            last = m.end()
        spans.append(ft.TextSpan(text[last:]))
        self.found_field.spans = spans
        self.update()

    def _highlight_replaced(self, text: str) -> None:
        spans: list[ft.TextSpan] = []
        last = 0
        for m in re.finditer(self.find_me, text):
            spans.append(ft.TextSpan(text[last : m.start()]))
            spans.append(
                ft.TextSpan(
                    m.expand(self.replace_me),
                    style=ft.TextStyle(bgcolor=ft.Colors.GREEN),
                )
            )
            last = m.end()
        spans.append(ft.TextSpan(text[last:]))
        self.replaced_field.spans = spans
        self.update()


class Data:
    """Database manager."""

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db_results: list[DpdHeadword] = []
        self._index: int = 0
        self._column_index: int = 0
        self.columns: list[str] = ["meaning_1", "meaning_2", "meaning_lit", "notes"]

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value: int) -> None:
        self._index = value

    @property
    def column_index(self) -> int:
        return self._column_index

    @column_index.setter
    def column_index(self, value: int) -> None:
        self._column_index = value

    @property
    def this_headword(self) -> DpdHeadword:
        return self.db_results[self.index]

    @property
    def this_field_name(self) -> str:
        return self.columns[self.column_index]

    @property
    def this_field_text(self) -> str:
        return getattr(self.this_headword, self.this_field_name) or ""

    def refresh_db_session(self) -> None:
        self.db_session.close()
        self.db_session = get_db_session(self.pth.dpd_db_path)

    def reset_state(self) -> None:
        """Reset all data state variables."""
        self._column_index = 0
        self._index = 0
        self.db_results = []

    def increment(self) -> None:
        """Move to next column, or next record if at last column."""
        last_column_index = len(self.columns) - 1
        if self.column_index == last_column_index:
            if self.index < len(self.db_results):
                self.column_index = 0
                self.index += 1
        else:
            self.column_index += 1

    def search_db(self, find_me: str) -> str:
        self.refresh_db_session()

        self.db_results = (
            self.db_session.query(DpdHeadword)
            .filter(
                or_(
                    DpdHeadword.meaning_1.regexp_match(find_me),
                    DpdHeadword.meaning_2.regexp_match(find_me),
                    DpdHeadword.meaning_lit.regexp_match(find_me),
                    DpdHeadword.notes.regexp_match(find_me),
                )
            )
            .all()
        )

        if len(self.db_results) > 0:
            return f"{len(self.db_results)} results found"
        return "No results found"

    def commit(self) -> None:
        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            raise e
