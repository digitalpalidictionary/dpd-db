import flet as ft

from db.inflections.generate_inflection_tables import InflectionsManager
from gui2.database_manager import DatabaseManager
from gui2.pass1_auto_controller import Pass1AutoController
from tools.ai_manager import AIManager


class Pass1AutoView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        db: DatabaseManager,
        ai_manager: AIManager,
    ) -> None:
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )
        self.page: ft.Page = page
        self.controller = Pass1AutoController(self, db, ai_manager)

        # Define constants
        LABEL_WIDTH: int = 150
        COLUMN_WIDTH: int = 700

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
            autofocus=True,
            options=self.book_options,
            width=300,
            text_size=14,
            border_color=ft.Colors.BLUE_200,
        )
        self.auto_processed_count_field = ft.TextField(
            "",
            expand=True,
        )
        self.word_in_text_field = ft.TextField(
            "",
            width=COLUMN_WIDTH,
            expand=True,
        )
        self.ai_results_field = ft.TextField(
            "",
            width=COLUMN_WIDTH,
            multiline=True,
            expand=True,
        )

        self.controls.extend(
            [
                ft.Row(
                    controls=[
                        ft.Text("", width=LABEL_WIDTH),
                        self.message_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("book", width=LABEL_WIDTH),
                        self.books_dropdown,
                        ft.ElevatedButton(
                            "AutoProcess Book",
                            on_click=self.handle_book_click,
                        ),
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
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("auto processed", width=LABEL_WIDTH),
                        self.auto_processed_count_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("word in text", width=LABEL_WIDTH),
                        self.word_in_text_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("ai results", width=LABEL_WIDTH),
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
