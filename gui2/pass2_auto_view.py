import flet as ft

from gui2.pass2_auto_control import Pass2AutoController
from gui2.toolkit import ToolKit

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=LABEL_COLOUR, size=10)


class Pass2AutoView(ft.Column):
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
        self.page: ft.Page = page
        self.controller = Pass2AutoController(
            self,
            toolkit,
        )
        self.controller.ui = self

        # Define controls
        self._message_field = ft.TextField(
            "",
            expand=True,
            label="Message",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_color=HIGHLIGHT_COLOUR,
            border_radius=20,
        )
        self.book_options = [
            ft.dropdown.Option(key=item, text=item)
            for item in self.controller.sc_books_list
        ]
        self.books_dropdown = ft.Dropdown(
            label="Book",
            label_style=TEXT_FIELD_LABEL_STYLE,
            autofocus=True,
            options=self.book_options,
            width=300,
            text_size=14,
            border_color=HIGHLIGHT_COLOUR,
            border_radius=20,
            hint_text="Select a book",
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
            options=self.ai_model_options,
            width=300,
            menu_width=500,
            text_size=14,
            border_color=HIGHLIGHT_COLOUR,
            border_radius=20,
            hint_text="Select AI Model",
        )
        self.auto_processed_count_field = ft.TextField(
            "",
            label="Counter",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=150,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
        )
        self.word_in_text_field = ft.TextField(
            "",
            expand=True,
            label="Word in text",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=HIGHLIGHT_COLOUR,
            border_radius=20,
        )
        self.gd_switch = ft.Switch(
            label="GD",
            value=True,
            on_change=self.handle_gd_toggle,
        )

        self.top_section = ft.Container(
            content=ft.Column(
                [
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
                            self.gd_switch,
                        ],
                    ),
                    ft.Row(
                        controls=[
                            self.word_in_text_field,
                            self.auto_processed_count_field,
                        ],
                    ),
                    ft.Row(
                        controls=[
                            self._message_field,
                        ],
                    ),
                ],
                spacing=10,
            ),
            border_radius=20,
            padding=ft.Padding(0, 10, 0, 0),
        )

        self.ai_results_field = ft.TextField(
            multiline=True,
            expand=True,
            border_width=0,
        )

        self.results_section = ft.Column(
            [
                self.ai_results_field,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.controls.append(self.top_section)
        self.controls.append(self.results_section)

    def handle_book_click(self, e: ft.ControlEvent):
        if self.books_dropdown.value:
            # Get selected AI model
            selected_model_str: str | None = self.ai_model_dropdown.value
            provider_preference: str | None = None
            model_name: str | None = None
            if selected_model_str:
                parts = selected_model_str.split("|", 1)
                if len(parts) == 2:
                    provider_preference, model_name = parts

            self.controller.auto_process_book(
                self.books_dropdown.value,
                provider_preference=provider_preference,
                model_name=model_name,
            )

    def handle_stop_click(self, e):
        self.controller.stop_flag = True
        self.update_message("stopping...")
        self.controller.processed_count = 0

    def handle_clear_click(self, e):
        self.clear_all_fields()

    def handle_gd_toggle(self, e):
        self.controller.gd_toggle = self.gd_switch.value

    def update_message(self, message: str):
        self._message_field.value = message
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
        self._message_field.value = ""
        self.auto_processed_count_field.value = ""
        self.ai_results_field.value = ""
        self.word_in_text_field.value = ""
        self.page.update()
