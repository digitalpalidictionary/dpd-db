import flet as ft
from rich import print

from gui2.database_manager import DatabaseManager
from gui2.dpd_fields import DpdFields
from gui2.dpd_fields_lists import PASS1_FIELDS
from gui2.mixins import PopUpMixin
from gui2.toolkit import ToolKit
from tools.sandhi_contraction import SandhiContractionFinder

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass1AddView(ft.Column, PopUpMixin):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        # Main column: expands, does NOT scroll
        super().__init__(
            expand=True,
            controls=[],
            spacing=5,
        )
        from gui2.pass1_add_controller import Pass1AddController

        PopUpMixin.__init__(self)
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        self.db: DatabaseManager = self.toolkit.db_manager
        self.controller = Pass1AddController(self, self.toolkit)
        self.dpd_fields: DpdFields
        self.sandhi_manager: SandhiContractionFinder = self.toolkit.sandhi_manager
        self.history_manager = self.toolkit.history_manager
        self.sandhi_dict = self.sandhi_manager.get_sandhi_contractions_simple()

        # --- Top Section Controls ---
        self.message_field = ft.Text("", color=HIGHLIGHT_COLOUR, selectable=True)
        self.book_options = [
            ft.dropdown.Option(key=item, text=item)
            for item in self.controller.pass1_books_list
        ]
        self.books_dropdown = ft.Dropdown(
            autofocus=True,
            options=self.book_options,
            width=300,
            text_size=14,
            border_color=HIGHLIGHT_COLOUR,
        )
        self.word_in_text = ft.TextField(
            value="",
            width=LABEL_WIDTH,
            color=HIGHLIGHT_COLOUR,
            expand=True,
        )
        self.remaining_to_process = ft.TextField(
            value="",
            width=LABEL_WIDTH,
            color=HIGHLIGHT_COLOUR,
            expand=True,
        )

        # Create the top section Column
        self.top_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("", width=LABEL_WIDTH),
                        self.message_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("book", width=LABEL_WIDTH, color=LABEL_COLOUR),
                        self.books_dropdown,
                        ft.ElevatedButton(
                            "Process Book",
                            width=BUTTON_WIDTH,
                            on_click=self.handle_process_book_click,
                        ),
                        ft.ElevatedButton(
                            "Refresh DB",
                            width=BUTTON_WIDTH,
                            on_click=self.handle_refresh_db_click,
                        ),
                        ft.ElevatedButton(
                            "Clear All",
                            width=BUTTON_WIDTH,
                            on_click=self.clear_all_fields,
                        ),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("word_in_text", width=LABEL_WIDTH, color=LABEL_COLOUR),
                        self.word_in_text,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("remaining", width=LABEL_WIDTH, color=LABEL_COLOUR),
                        self.remaining_to_process,
                    ],
                ),
            ],
            spacing=5,
        )

        # Initialize middle section
        self.middle_section = self._build_middle_section()

        self.bottom_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Add to DB",
                                on_click=self.handle_add_to_db_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Pass",
                                on_click=self.handle_pass_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Delete",
                                on_click=self.handle_delete_click,
                                width=BUTTON_WIDTH,
                            ),
                        ],
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Sandhi OK",
                                on_click=self.handle_sandhi_ok_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Add to Sandhi",
                                on_click=self.handle_add_to_sandhi_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Add to Variants",
                                on_click=self.handle_add_to_variants_click,
                                width=BUTTON_WIDTH,
                            ),
                            ft.ElevatedButton(
                                "Add to Spelling mistakes",
                                on_click=self.handle_add_to_spelling_mistakes_click,
                                width=BUTTON_WIDTH,
                            ),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(10),
        )

        # --- Set Main View Controls ---
        self.controls = [
            self.top_section,
            self.middle_section,
            self.bottom_section,
        ]

    def load_database(self) -> None:
        self.controller.db.make_inflections_lists()

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def update_remaining(self, message: str):
        self.remaining_to_process.value = message
        self.page.update()

    def handle_process_book_click(self, e: ft.ControlEvent) -> None:
        if self.books_dropdown.value:
            self.controller.process_book(self.books_dropdown.value)

    def handle_refresh_db_click(self, e: ft.ControlEvent) -> None:
        self.db.new_db_session()
        self.update_message("Database refreshed")

    def handle_add_to_db_click(self, e: ft.ControlEvent) -> None:
        self.controller.make_dpd_headword_and_add_to_db()

    def handle_add_to_sandhi_click(self, e: ft.ControlEvent) -> None:
        current_word = self.word_in_text.value
        if not current_word:
            self.update_message("No word selected.")
            return

        self.show_popup(
            page=self.page,
            prompt_message="Enter construction",
            initial_value=self.word_in_text.value or "",
            on_submit=self.process_sandhi_popup_result,
        )

    def handle_sandhi_ok_click(self, e: ft.ControlEvent):
        current_word = self.word_in_text.value
        if current_word:
            self.controller.update_sandhi_checked(current_word)
            self.update_message(f"{current_word} added to sandhi checked")

    def handle_add_to_variants_click(self, e: ft.ControlEvent):
        current_word = self.word_in_text.value
        if not current_word:
            self.update_message("No word selected.")
            return

        self.show_popup(
            page=self.page,
            prompt_message=f"Enter main reading for {current_word}",
            initial_value=self.word_in_text.value or "",
            on_submit=self.process_variant_popup_result,
        )

    def handle_add_to_spelling_mistakes_click(self, e: ft.ControlEvent):
        current_word = self.word_in_text.value
        if not current_word:
            self.update_message("No word selected.")
            return

        self.show_popup(
            page=self.page,
            prompt_message=f"Enter correct spelling for {current_word}",
            initial_value=self.word_in_text.value or "",
            on_submit=self.process_spelling_popup_result,
        )

    def handle_pass_click(self, e: ft.ControlEvent) -> None:
        self.clear_all_fields()
        self.controller.get_next_item()
        self.controller.load_into_gui()

    def handle_delete_click(self, e: ft.ControlEvent) -> None:
        print(self.dpd_fields)
        if self.word_in_text.value:
            self.controller.remove_word_and_save_json()
            self.clear_all_fields()
            self.controller.get_next_item()
            self.controller.load_into_gui()
        else:
            self.update_message("No word_in_text.")

    def _build_middle_section(self) -> ft.Column:
        """Build and return the middle section with DpdFields."""
        self.dpd_fields = DpdFields(
            self,
            self.db,
            self.sandhi_dict,
            {},  # empty hyphenations_dict
            simple_examples=True,
        )
        middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )

        # Use the imported list
        visible_fields = PASS1_FIELDS

        self.dpd_fields.add_to_ui(middle_section, visible_fields=visible_fields)
        return middle_section

    def clear_all_fields(self, e: ft.ControlEvent | None = None) -> None:
        """Clear all fields by rebuilding the middle section."""
        # Rebuild middle section
        self.middle_section = self._build_middle_section()

        # Update view controls with new middle section
        self.controls = [self.top_section, self.middle_section, self.bottom_section]

        # Clear word_in_text separately
        self.word_in_text.value = ""
        self.word_in_text.error_text = None

        self.update_message("")
        self.page.update()

    def process_sandhi_popup_result(self, breakup_value: str | None) -> None:
        """Handles the result after the sandhi popup closes."""

        if breakup_value is not None and self.word_in_text.value:
            self.controller.update_sandhi_corrections(
                self.word_in_text.value, breakup_value
            )
            self.update_message(f"Sandhi added for {self.word_in_text.value}")
        else:
            self.update_message("Sandhi input cancelled.")

    def process_variant_popup_result(self, main_reading: str | None) -> None:
        """Handles the result after the variant popup closes."""

        if main_reading is not None and self.word_in_text.value:
            self.controller.variants.update_and_save(
                self.word_in_text.value, main_reading
            )
            self.update_message(f"Variant added for {self.word_in_text.value}")
        else:
            self.update_message("Variant input cancelled.")

    def process_spelling_popup_result(self, correct_spelling: str | None) -> None:
        """Handles the result after the spelling popup closes."""

        if correct_spelling is not None and self.word_in_text.value:
            self.controller.spelling_mistakes.update_and_save(
                self.word_in_text.value, correct_spelling
            )
            self.update_message(
                f"Spelling correction added for {self.word_in_text.value}"
            )
        else:
            self.update_message("Spelling input cancelled.")
