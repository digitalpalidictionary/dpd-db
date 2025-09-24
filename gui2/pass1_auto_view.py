import flet as ft

from db.inflections.generate_inflection_tables import InflectionsManager
from gui2.pass1_auto_controller import Pass1AutoController
from gui2.toolkit import ToolKit

LABEL_WIDTH = 250
COLUMN_WIDTH: int = 700
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=LABEL_COLOUR, size=10)


class Pass1AutoView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )
        self.page: ft.Page = page
        self.controller = Pass1AutoController(
            self,
            toolkit,
        )

        # Define controls
        self.message_field = ft.Text(
            "",
            expand=True,
            color=ft.Colors.BLUE_200,
            selectable=True,
        )
        self.book_options = [
            ft.dropdown.Option(key=item, text=item)
            for item in self.controller.pass1_books_list
        ]
        self.books_dropdown = ft.Dropdown(
            label="Book",
            label_style=TEXT_FIELD_LABEL_STYLE,
            autofocus=True,
            options=self.book_options,
            width=300,
            text_size=14,
            border_color=ft.Colors.BLUE_200,
            border_radius=10,
        )
        self.ai_model_options = [
            ft.dropdown.Option(
                key=f"{provider}|{model_name}", text=f"{provider}: {model_name}"
            )
            for provider, model_name, wait_time in toolkit.ai_manager.DEFAULT_MODELS
        ]
        self.ai_model_dropdown = ft.Dropdown(
            label="AI Model",
            label_style=TEXT_FIELD_LABEL_STYLE,
            autofocus=True,
            options=self.ai_model_options,
            width=300,
            text_size=14,
            border_color=ft.Colors.BLUE_200,
            border_radius=10,
            menu_width=700,
        )
        self.auto_processed_count_field = ft.TextField(
            "",
            label="Counter",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=200,
            color=HIGHLIGHT_COLOUR,
            border_radius=10,
        )
        self.gd_switch = ft.Switch(
            label="GD",
            value=True,
            on_change=self.handle_gd_toggle,
        )
        self.word_in_text_field = ft.TextField(
            "",
            expand=True,
            label="Word in text",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_radius=10,
        )
        self.ai_results_field = ft.TextField(
            "",
            width=COLUMN_WIDTH,
            multiline=True,
            expand=True,
            label="Results",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_radius=10,
        )

        self.controls.extend(
            [
                ft.Row(
                    controls=[
                        self.message_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        self.books_dropdown,
                        ft.ElevatedButton(
                            "AutoProcess Book",
                            on_click=self.handle_book_click,
                        ),
                        self.ai_model_dropdown,
                        ft.ElevatedButton(
                            "Stop",
                            on_click=self.handle_stop_click,
                        ),
                        ft.ElevatedButton(
                            "Clear",
                            on_click=self.handle_clear_click,
                        ),
                        ft.ElevatedButton(
                            "Update inflections",
                            on_click=self.handle_update_inflections_click,
                        ),
                        self.gd_switch,
                    ],
                ),
                ft.Row(
                    controls=[
                        self.word_in_text_field,
                        self.auto_processed_count_field,
                    ],
                ),
                ft.Divider(),
                ft.Row(
                    controls=[
                        self.ai_results_field,
                    ]
                ),
            ]
        )

    def handle_book_click(self, e):
        if self.books_dropdown.value:
            self.controller.auto_process_book(self.books_dropdown.value)

    def handle_stop_click(self, e):
        self.controller.stop_flag = True

    def handle_clear_click(self, e):
        self.clear_all_fields()

    def handle_update_inflections_click(self, e):
        self.update_message("updating inflections...")
        inflections_manager = InflectionsManager()
        inflections_manager.run()
        self.controller.db.make_inflections_lists()
        self.update_message("inflections updated")

    def handle_gd_toggle(self, e):
        self.controller.gd_toggle = self.gd_switch.value

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def update_ai_results(self, results: str):
        self.ai_results_field.value = results
        self.page.update()

    def update_word_in_text(self, word: str):
        self.word_in_text_field.value = word
        self.page.update()

    def update_auto_processed_count(self, count: str):
        self.auto_processed_count_field.value = str(count)
        self.page.update()

    def clear_all_fields(self):
        self.message_field.value = ""
        self.auto_processed_count_field.value = ""
        self.books_dropdown.value = ""
        self.ai_results_field.value = ""
        self.word_in_text_field.value = ""
        self.page.update()
