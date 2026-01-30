import re

import flet as ft
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
        self.phase: int = 1  # 1 = regular search, 2 = bold search

        # UI elements
        self.find_text = ft.TextField(
            "",
            width=400,
            on_blur=self.handle_find_blur,
        )
        self.replace_text = ft.TextField("", width=400)
        self.find_button = ft.ElevatedButton("Find", on_click=self.find_clicked)
        self.clear_button = ft.ElevatedButton("Clear", on_click=self.clear_search)
        self.message = ft.Text("", expand=True)
        self.found_field = ft.Text(width=800, expand=True, selectable=True)
        self.replaced_field_text = ft.Text(width=800, expand=True, selectable=True)
        self.replaced_field_input = ft.TextField(
            "", width=800, expand=True, multiline=True, disabled=True
        )
        self.replaced_field = self.replaced_field_text  # Reference to current widget
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

    def _set_replaced_field_mode(self, editable: bool):
        """Set the replaced field to be editable (TextField) or read-only (Text)."""

        # Find the row containing the replaced field (line 87-92 in the UI structure)
        replaced_row = self._middle_section.content.controls[
            2
        ]  # The row with "Replaced:" label

        if editable:
            # Switch to editable mode (TextField)
            current_value = getattr(self.replaced_field, "value", "")
            self.replaced_field_input.value = current_value
            self.replaced_field_input.disabled = False
            self.replaced_field = self.replaced_field_input
            # Update the UI to show the TextField instead of Text
            replaced_row.controls[1] = self.replaced_field_input
            self.update()
        else:
            # Switch to read-only mode (Text)
            current_value = getattr(self.replaced_field, "value", "")
            self.replaced_field_text.value = current_value
            self.replaced_field_text.spans = []  # Clear any existing spans
            self.replaced_field = self.replaced_field_text
            # Update the UI to show the Text instead of TextField
            replaced_row.controls[1] = self.replaced_field_text
            self.update()

    def update_message(self, text: str):
        self.message.value = text
        self.update()

    def _reset_state(self):
        """Reset all state variables to start a fresh search."""
        self.phase = 1
        self.data.reset_state()

    def clear_fields(self):
        self.found_field.value = ""
        self.found_field.spans = []
        self.replaced_field_text.value = ""
        self.replaced_field_text.spans = []
        self.replaced_field_input.value = ""
        # Reset replaced_field to disabled state
        self.replaced_field_input.disabled = True
        self.update()

    def clear_search(self, e):
        self.find_text.value = ""
        self.replace_text.value = ""
        self.message.value = ""
        self.found_field.value = ""
        self.replaced_field.value = ""
        # Reset replaced_field to disabled state
        if self.replaced_field != self.replaced_field_text:
            self._set_replaced_field_mode(editable=False)
        self.replaced_field_text.value = ""
        self.replaced_field_input.value = ""
        # Reset to clean state
        self._reset_state()
        self.update()

    def find_clicked(self, e):
        if self.find_text.value and self.replace_text.value:
            self.update_message("")
            self.find_me = self.find_text.value
            self.replace_me = self.replace_text.value
            # Always start from a clean slate
            self._reset_state()
            self._initiate_find_replace()
        else:
            self.update_message("Please enter both find and replace values")

    def _initiate_phase_2(self):
        self.phase = 2
        self.data.set_phase(2)
        message = self.data.search_db_bold(self.find_me)
        if len(self.data.db_results) > 0:
            self.update_message(message)
            self._load_next_result()
        else:
            self.update_message("No bold results found")
            self.clear_fields()

    def _initiate_find_replace(self):
        if self.phase == 1:
            message = self.data.search_db(self.find_me)
            if len(self.data.db_results) > 0:
                self.update_message(message)
                self._load_next_result()
            else:
                self.update_message("No results found, checking for bold entries...")
                # Automatically transition to Phase 2
                self._initiate_phase_2()
        else:  # Phase 2
            self._initiate_phase_2()

    def _load_next_result(self):
        if self.data.index >= len(self.data.db_results):
            if self.phase == 1:
                # End of Phase 1, automatically start Phase 2
                self.update_message("Phase 1 complete, starting Phase 2...")
                self._initiate_phase_2()
                return
            else:
                self.update_message("End of results")
                self.clear_fields()
                # Reset to clean state for next search
                self._reset_state()
                return

        self.update_message(
            f"Phase {self.phase}: {self.data.index + 1}/{len(self.data.db_results)} {self.data.this_field_name}"
        )

        if self.phase == 1:
            # Phase 1 logic (existing)
            if re.findall(self.find_me, self.data.this_field_text):
                self._highlight_found(self.data.this_field_text)
                # Ensure we're in read-only mode for phase 1
                if self.replaced_field != self.replaced_field_text:
                    self._set_replaced_field_mode(editable=False)
                self._highlight_replaced(self.data.this_field_text)
            else:
                self._increment()
        else:
            # Phase 2 logic (bold search)
            field_text = self.data.this_field_text
            bold_pattern = "".join(
                [rf"(?:<b>)?{re.escape(char)}(?:</b>)?" for char in self.find_me]
            )

            if re.search(bold_pattern, field_text):
                self._highlight_found(field_text)
                # For Phase 2, show the actual field content in replaced_field (not auto-replaced)
                # Make replaced_field editable
                self._set_replaced_field_mode(editable=True)
                self.replaced_field.value = field_text
                # Also highlight the replaced text (with the replacement)
                self._highlight_replaced(field_text)
                self.update()
            else:
                self._increment()

    def _increment(self):
        # Move to next column, or next record if at last column
        self.data.increment()
        self._load_next_result()

    def commit_clicked(self, e):
        if self.phase == 1:
            # Phase 1 logic (existing)
            new_value = re.sub(self.find_me, self.replace_me, self.data.this_field_text)
            setattr(self.data.this_headword, self.data.this_field_name, new_value)
            self.data.commit()
            self._increment()
        else:
            # Phase 2 logic (manual edit)
            # Save the edited content from replaced_field
            new_value = self.replaced_field.value
            setattr(self.data.this_headword, self.data.this_field_name, new_value)
            self.data.commit()
            self._increment()

    def ignore_clicked(self, e):
        self._increment()
        self._load_next_result()

    def handle_find_blur(self, e: ft.ControlEvent):
        """Copy find text to replace text when user exits find field."""
        if self.find_text.value and not self.replace_text.value:
            self.replace_text.value = self.find_text.value
            self.update()

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

        # Apply spans to the appropriate widget
        if self.replaced_field == self.replaced_field_text:
            self.replaced_field_text.spans = spans
        else:
            # TextField doesn't support spans, so we'll just show the text as is
            pass
        self.update()


class Data:
    """Database manager."""

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db_results: list[DpdHeadword] = []
        self._index: int = 0
        self._column_index: int = 0
        self.columns: list[str] = ["example_1", "example_2", "commentary"]
        self.phase: int = 1  # 1 = regular search, 2 = bold search

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
        return getattr(self.this_headword, self.this_field_name)

    def refresh_db_session(self):
        self.db_session.close()
        self.db_session = get_db_session(self.pth.dpd_db_path)

    def reset_state(self) -> None:
        """Reset all data state variables."""
        self.phase = 1
        self._column_index = 0
        self._index = 0
        self.db_results = []

    def set_phase(self, phase: int) -> None:
        """Set the search phase."""
        self.phase = phase

    def increment(self) -> None:
        """Move to next column, or next record if at last column."""
        last_column_index = len(self.columns) - 1
        if self.column_index == last_column_index:
            if self.index < len(self.db_results):
                self.column_index = 0
                self.index += 1
        else:
            self.column_index += 1

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

    def search_db_bold(self, find_me: str) -> str:
        self.refresh_db_session()

        # Pattern to match text with bold tags
        bold_pattern = "".join(
            [rf"(?:<b>)?{re.escape(char)}(?:</b>)?" for char in find_me]
        )

        self.db_results = (
            self.db_session.query(DpdHeadword)
            .filter(
                or_(
                    DpdHeadword.example_1.regexp_match(bold_pattern),
                    DpdHeadword.example_2.regexp_match(bold_pattern),
                    DpdHeadword.commentary.regexp_match(bold_pattern),
                )
            )
            .all()
        )

        if len(self.db_results) > 0:
            return f"{len(self.db_results)} bold results found"
        return "No bold results found"
