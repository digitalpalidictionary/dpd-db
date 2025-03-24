import flet as ft


class Gui:
    def __init__(self, page: ft.Page):
        self.page: ft.Page = page
        self.page.title = "DB Tests GUI"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.START

        self.page.padding = 20
        self.column_width = 350

        self.page.on_keyboard_event = self.on_keyboard

        # window
        self.page.window.maximized = True

        # buttons
        self.run_tests_button = ft.ElevatedButton(text="Run", width=200, height=50)
        self.stop_tests_button = ft.ElevatedButton(text="Stop", width=200, height=50)
        self.edit_test_button = ft.ElevatedButton(text="Edit", width=200, height=50)
        self.update_tests_button = ft.ElevatedButton(
            text="Update", width=200, height=50
        )
        self.add_test_button = ft.ElevatedButton(text="Add", width=200, height=50)
        self.delete_test_button = ft.ElevatedButton(text="Delete", width=200, height=50)

        # fields
        self.test_number = ft.TextField(label="", width=100)
        self.test_name = ft.TextField(label="", width=850)
        self.iterations = ft.TextField("", width=100)

        self.search_column_1 = ft.TextField("", width=self.column_width)
        self.search_sign_1 = ft.TextField("", width=self.column_width)
        self.search_string_1 = ft.TextField("", width=self.column_width)

        self.search_column_2 = ft.TextField("", width=self.column_width)
        self.search_sign_2 = ft.TextField("", width=self.column_width)
        self.search_string_2 = ft.TextField("", width=self.column_width)

        self.search_column_3 = ft.TextField("", width=self.column_width)
        self.search_sign_3 = ft.TextField("", width=self.column_width)
        self.search_string_3 = ft.TextField("", width=self.column_width)

        self.search_column_4 = ft.TextField("", width=self.column_width)
        self.search_sign_4 = ft.TextField("", width=self.column_width)
        self.search_string_4 = ft.TextField("", width=self.column_width)

        self.search_column_5 = ft.TextField("", width=self.column_width)
        self.search_sign_5 = ft.TextField("", width=self.column_width)
        self.search_string_5 = ft.TextField("", width=self.column_width)

        self.search_column_6 = ft.TextField("", width=self.column_width)
        self.search_sign_6 = ft.TextField("", width=self.column_width)
        self.search_string_6 = ft.TextField("", width=self.column_width)

        self.error_column = ft.TextField("", width=self.column_width)
        self.exceptions = ft.TextField("", width=self.column_width)
        self.exceptions_add_button = ft.ElevatedButton("Add", width=150, height=50)

        self.display_1 = ft.TextField("", width=self.column_width)
        self.display_2 = ft.TextField("", width=self.column_width)
        self.display_3 = ft.TextField("", width=self.column_width)

        self.test_results = ft.ListView(width=1000, height=500)

        self.next_button = ft.ElevatedButton(text="Next", width=1100, height=50)
        self.layout = self.make_layout()
        self.page.add(self.layout)
        self.page.update()

    def make_layout(self):
        buttons_column = ft.Column(
            [
                self.run_tests_button,
                self.stop_tests_button,
                self.edit_test_button,
                self.add_test_button,
                self.update_tests_button,
                self.delete_test_button,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            width=350,
            expand=True,
            expand_loose=True,
        )

        tests_column = ft.Column(
            [
                ft.Row(
                    [
                        self.label(""),
                        self.test_number,
                        self.test_name,
                        self.iterations,
                    ]
                ),
                ft.Row(
                    [
                        self.label("test1"),
                        self.search_column_1,
                        self.search_sign_1,
                        self.search_string_1,
                    ]
                ),
                ft.Row(
                    [
                        self.label("test2"),
                        self.search_column_2,
                        self.search_sign_2,
                        self.search_string_2,
                    ]
                ),
                ft.Row(
                    [
                        self.label("test3"),
                        self.search_column_3,
                        self.search_sign_3,
                        self.search_string_3,
                    ]
                ),
                ft.Row(
                    [
                        self.label("test4"),
                        self.search_column_4,
                        self.search_sign_4,
                        self.search_string_4,
                    ]
                ),
                ft.Row(
                    [
                        self.label("test5"),
                        self.search_column_5,
                        self.search_sign_5,
                        self.search_string_5,
                    ]
                ),
                ft.Row(
                    [
                        self.label("test6"),
                        self.search_column_6,
                        self.search_sign_6,
                        self.search_string_6,
                    ]
                ),
                ft.Row(
                    [
                        self.label("display"),
                        self.display_1,
                        self.display_2,
                        self.display_3,
                    ]
                ),
                ft.Row(
                    [
                        self.label("exceptions"),
                        self.exceptions,
                        self.exceptions_add_button,
                    ]
                ),
                ft.Row(
                    [
                        self.label("results"),
                        self.test_results,
                    ]
                ),
                ft.Row(
                    [
                        self.label(""),
                        self.next_button,
                    ]
                ),
            ]
        )

        layout = ft.Container(
            content=ft.Row(
                [
                    buttons_column,
                    tests_column,
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )
        return layout

    def label(self, label):
        return ft.Text(label, width=100)

    def on_keyboard(self, e: ft.KeyboardEvent):
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

        if e.key == " ":
            print("Next")


def main(page: ft.Page):
    Gui(page)


# Start the app
ft.app(target=main)
