import flet as ft

from gui2.class_database import DatabaseManager
from gui2.class_mixins import PopUpMixin
from gui2.class_dpd_fields import DpdFields
from gui2.class_pass2_file_manager import Pass2AutoFileManager

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class EditView(ft.Column, PopUpMixin):
    def __init__(self, page: ft.Page, db: DatabaseManager) -> None:
        # Main container column - does not scroll, expands vertically
        super().__init__(
            expand=True,  # Main column expands
            controls=[],  # Controls defined below
            spacing=5,
        )
        self.page: ft.Page = page
        self._db = db
        self._pass2_auto_file_manager = Pass2AutoFileManager()

        self._message_field = ft.Text("", expand=True)
        self._next_pass2_auto_button = ft.ElevatedButton(
            "NextPass2Auto",
            width=BUTTON_WIDTH,
            on_click=self._click_load_next_pass2_entry,
        )
        self._enter_id_or_lemma_field = ft.TextField(
            "",
            width=400,
            expand=True,
            expand_loose=True,
            on_submit=self._click_edit_headword,
        )
        self._clone_headword_button = ft.ElevatedButton(
            "Clone", on_click=self._click_clone_headword
        )
        self._edit_headword_button = ft.ElevatedButton(
            "Edit", on_click=self._click_edit_headword
        )

        self._top_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            # self._clone_headword_button,
                            self._enter_id_or_lemma_field,
                            self._edit_headword_button,
                            self._next_pass2_auto_button,
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row(controls=[self._message_field]),
                ],
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
        )

        self._dpd_fields = DpdFields(self, self._db)
        self._middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO, expand=True, spacing=5
        )
        self._dpd_fields.add_to_ui(self._middle_section, include_add_fields=True)

        self._bottom_section = ft.Container(
            content=ft.Text("Bottom Section Placeholder"),  # Example content
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
        )

        self.controls = [
            self._top_section,
            self._middle_section,
            self._bottom_section,
        ]

    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()

    def _click_edit_headword(self, e: ft.ControlEvent) -> None:
        id_or_lemma = self._enter_id_or_lemma_field.value

        if id_or_lemma:
            headword = self._db.get_headword_by_id_or_lemma(id_or_lemma)
            if headword:
                self.clear_all_fields()
                self.headword = headword
                self._dpd_fields.update_db_fields(headword)
                self.update_message(f"loaded {self.headword.lemma_1}")
                if str(self.headword.id) in self._pass2_auto_file_manager.responses:
                    to_add = self._pass2_auto_file_manager.get_headword(
                        str(self.headword.id)
                    )
                    self._dpd_fields.update_add_fields(to_add)
            else:
                self.update_message("headword not found")
        else:
            self.update_message("you're shooting blanks")

    def _click_clone_headword(self, e: ft.ControlEvent) -> None:
        pass

    def _click_load_next_pass2_entry(self, e: ft.ControlEvent | None = None) -> None:
        """Load next pass2 entry into the view."""
        headword_id, pass2_auto_data = (
            self._pass2_auto_file_manager.get_next_headword_data()
        )

        if headword_id is not None:
            self._dpd_fields.clear_fields()

            self.headword = self._db.get_headword_by_id(int(headword_id))
            if self.headword is not None:
                self._dpd_fields.update_db_fields(self.headword)

            self._dpd_fields.update_add_fields(pass2_auto_data)

        else:
            self._message_field.value = "Current Pass2: None"
            self._dpd_fields.clear_fields(target="all")  # Clear all fields

        self.update()

    def clear_all_fields(self):
        self._dpd_fields.clear_fields(target="all")
