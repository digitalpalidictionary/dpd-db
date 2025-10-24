import re

import flet as ft

from gui2.database_manager import DatabaseManager
from gui2.mixins import PopUpMixin
from gui2.sandhi_files_manager import SandhiFileManager
from gui2.toolkit import ToolKit

FIELD_WIDTH = 700
BUTTON_WIDTH = 150
LABEL_WIDTH = 200
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=LABEL_COLOUR, size=10)


class SandhiView(ft.Column, PopUpMixin):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        super().__init__(
            expand=True,
            controls=[],
            spacing=5,
        )
        PopUpMixin.__init__(self)
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit
        self.db: DatabaseManager = self.toolkit.db_manager
        self.sandhi_files_manager: SandhiFileManager = self.toolkit.sandhi_files_manager

        self.message_field = ft.TextField(
            expand=True,
            border_radius=20,
            text_style=ft.TextStyle(color=ft.Colors.BLUE_200),
        )

        # Section 1: Sandhi OK
        self.sandhi_ok_word = ft.TextField(
            label="Sandhi OK",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_sandhi_ok_click,
        )
        self.sandhi_ok_button = ft.ElevatedButton(
            "Add",
            width=BUTTON_WIDTH,
            on_click=self.handle_sandhi_ok_click,
        )

        # Section 2: Add to Sandhi
        self.sandhi_word = ft.TextField(
            label="Sandhi",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH / 2 - 5,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_add_to_sandhi_click,
        )
        self.sandhi_correction = ft.TextField(
            label="Correction",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH / 2 - 5,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_add_to_sandhi_click,
        )
        self.add_to_sandhi_button = ft.ElevatedButton(
            "Add",
            width=BUTTON_WIDTH,
            on_click=self.handle_add_to_sandhi_click,
        )

        # Section 3: Bulk Add
        self.bulk_add_list = ft.TextField(
            label="Bulk Add",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            multiline=False,
            on_submit=self.handle_bulk_add_click,
        )
        self.bulk_add_button = ft.ElevatedButton(
            "Add",
            width=BUTTON_WIDTH,
            on_click=self.handle_bulk_add_click,
        )

        # Section 4: Add to Variants
        self.variant_word = ft.TextField(
            label="Word",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH / 2 - 5,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_add_to_variants_click,
        )
        self.variant_main_reading = ft.TextField(
            label="Main Reading",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH / 2 - 5,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_add_to_variants_click,
        )
        self.add_to_variants_button = ft.ElevatedButton(
            "Add",
            width=BUTTON_WIDTH,
            on_click=self.handle_add_to_variants_click,
        )

        # Section 5: Add to Spelling Mistakes
        self.spelling_mistake_word = ft.TextField(
            label="Word",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH / 2 - 5,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_add_to_spelling_mistakes_click,
        )
        self.spelling_mistake_correction = ft.TextField(
            label="Correction",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=FIELD_WIDTH / 2 - 5,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
            on_submit=self.handle_add_to_spelling_mistakes_click,
        )
        self.add_to_spelling_mistakes_button = ft.ElevatedButton(
            "Add",
            width=BUTTON_WIDTH,
            on_click=self.handle_add_to_spelling_mistakes_click,
        )

        self.controls = [
            ft.Row(controls=[self.message_field]),
            ft.Divider(height=10, color=HIGHLIGHT_COLOUR),
            ft.Row(
                controls=[
                    ft.Text("sandhi ok", width=LABEL_WIDTH),
                    self.sandhi_ok_word,
                    self.sandhi_ok_button,
                ]
            ),
            ft.Divider(height=10, color=HIGHLIGHT_COLOUR),
            ft.Row(
                controls=[
                    ft.Text("sandhi manual", width=LABEL_WIDTH),
                    self.sandhi_word,
                    self.sandhi_correction,
                    self.add_to_sandhi_button,
                ]
            ),
            ft.Divider(height=10, color=HIGHLIGHT_COLOUR),
            ft.Row(
                controls=[
                    ft.Text("sandhi bulk", width=LABEL_WIDTH),
                    self.bulk_add_list,
                    self.bulk_add_button,
                ]
            ),
            ft.Divider(height=10, color=HIGHLIGHT_COLOUR),
            ft.Row(
                controls=[
                    ft.Text("variant", width=LABEL_WIDTH),
                    self.variant_word,
                    self.variant_main_reading,
                    self.add_to_variants_button,
                ]
            ),
            ft.Divider(height=10, color=HIGHLIGHT_COLOUR),
            ft.Row(
                controls=[
                    ft.Text("spelling", width=LABEL_WIDTH),
                    self.spelling_mistake_word,
                    self.spelling_mistake_correction,
                    self.add_to_spelling_mistakes_button,
                ]
            ),
        ]

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def handle_sandhi_ok_click(self, e: ft.ControlEvent):
        current_word = self.sandhi_ok_word.value
        if current_word:
            self.sandhi_files_manager.add_sandhi_to_checked_csv(current_word)
            self.update_message(f"{current_word} added to sandhi checked")
            self.sandhi_ok_word.value = ""
            self.page.update()

    def handle_add_to_sandhi_click(self, e: ft.ControlEvent) -> None:
        sandhi_word = self.sandhi_word.value
        correction = self.sandhi_correction.value
        if sandhi_word and correction:
            self.sandhi_files_manager.update_sandhi_corrections_csv(
                sandhi_word, correction
            )
            self.update_message(f"Sandhi added for {sandhi_word}")
            self.sandhi_word.value = ""
            self.sandhi_correction.value = ""
            self.page.update()
        else:
            self.update_message("Both sandhi and correction fields are required.")

    def handle_bulk_add_click(self, e: ft.ControlEvent):
        word_list_str = self.bulk_add_list.value
        if word_list_str:
            try:
                # Process the string to get a list of words
                cleaned_str = re.sub(r"['\"\,\;\[\]\{\}]", " ", word_list_str)
                words = cleaned_str.split()

                for word in words:
                    if word:
                        self.sandhi_files_manager.add_sandhi_to_checked_csv(word)

                self.update_message(f"Bulk added {len(words)} words to sandhi checked.")
                self.bulk_add_list.value = ""
                self.page.update()

            except Exception as ex:
                self.update_message(f"Error processing bulk add: {ex}")
                self.page.update()

    def handle_add_to_variants_click(self, e: ft.ControlEvent) -> None:
        word = self.variant_word.value
        main_reading = self.variant_main_reading.value
        if word and main_reading:
            self.sandhi_files_manager.add_variant(word, main_reading)
            self.update_message(f"Variant '{main_reading}' added for '{word}'")
            self.variant_word.value = ""
            self.variant_main_reading.value = ""
            self.page.update()
        else:
            self.update_message("Both word and main reading fields are required.")

    def handle_add_to_spelling_mistakes_click(self, e: ft.ControlEvent) -> None:
        word = self.spelling_mistake_word.value
        correction = self.spelling_mistake_correction.value
        if word and correction:
            self.sandhi_files_manager.add_spelling_mistake(word, correction)
            self.update_message(f"Spelling correction '{correction}' added for '{word}'")
            self.spelling_mistake_word.value = ""
            self.spelling_mistake_correction.value = ""
            self.page.update()
        else:
            self.update_message("Both word and correction fields are required.")
