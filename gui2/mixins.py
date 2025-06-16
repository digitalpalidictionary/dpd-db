# -*- coding: utf-8 -*-
from tools.paths import ProjectPaths
import flet as ft


class SandhiOK:
    """Requires pth = ProjectPaths()"""

    pth = ProjectPaths()

    def update_sandhi_corrections(self, sandhi: str, breakup: str):
        """
        Updates `shared_data/deconstructor/checked.csv`
        and `shared_data/deconstructor/manual_corrections.tsv`

        `sandhi` is the word as it appears in a text: `aniccomhi`

        `breakup` is seperated by plus signs: `anicco + amhi`
        """
        with open(self.pth.decon_manual_corrections, "a") as f:
            f.write(f"{sandhi}\t{breakup}\n")
        with open(self.pth.decon_checked, "a") as f:
            f.write(f"{sandhi}\n")

    def update_sandhi_checked(self, sandhi: str):
        """
        Updates `shared_data/deconstructor/checked.csv`
        """
        with open(self.pth.decon_checked, "a") as f:
            f.write(f"{sandhi}\n")


class PopUpMixin:
    def __init__(self):
        self._popup_textfield = ft.TextField(
            label="Enter value",
            autofocus=True,
            width=1000,
        )
        self._dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Column(
                    [self._popup_textfield],
                ),
                width=500,
                height=100,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._handle_popup_close,
                ),
                ft.TextButton(
                    "OK",
                    on_click=self._handle_popup_ok,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.popup_result = None
        self._current_page = None
        self._callback_on_ok = None

    def _handle_popup_ok(self, e):
        self.popup_result = self._popup_textfield.value
        print(f"Value entered: {self.popup_result}")
        self._dialog.open = False
        if self._current_page:
            self._current_page.update()
        if self._callback_on_ok and callable(self._callback_on_ok):
            self._callback_on_ok(self.popup_result)

    def _handle_popup_close(self, e):
        self.popup_result = None
        self._dialog.open = False
        if self._current_page:
            self._current_page.update()
        if self._callback_on_ok and callable(self._callback_on_ok):
            self._callback_on_ok(None)

    def show_popup(
        self,
        page: ft.Page,
        prompt_message: str = "Enter value",
        initial_value: str = "",
        on_submit=None,
    ):
        self._current_page = page
        self.popup_result = None
        self._callback_on_ok = on_submit
        self._popup_textfield.label = prompt_message
        self._popup_textfield.value = initial_value
        page.open(self._dialog)
        page.update()


class SnackBarMixin:
    """Mixin class to provide a standardized way to show SnackBars."""

    def show_snackbar(
        self,
        page: ft.Page,
        message: str,
    ):
        """Displays a SnackBar message at the bottom of the page.

        Args:
            page: The ft.Page object.
            message: The text message to display.
            bgcolor: The background color of the SnackBar (defaults to GREEN).
            duration: How long the SnackBar stays visible in milliseconds (defaults to 4000).
        """
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.BLACK),
            bgcolor=ft.Colors.BLUE_200,
            duration=3000,
        )
        page.open(snackbar)
        page.update()


# here's a good example of two field popup

#     self.book_input = ft.TextField(
#         hint_text="book", autofocus=True
#     )  # TODO how to make on_submit jump to the next word?
#     self.word_input = ft.TextField(
#         hint_text="word", on_submit=self.click_book_and_word_ok
#     )

#     self.get_book_and_word_dialog = ft.AlertDialog(
#         modal=True,
#         content=ft.Column(
#             height=150,
#             controls=[self.book_input, self.word_input],
#         ),
#         alignment=ft.alignment.center,
#         title_padding=ft.padding.all(25),
#         actions=[
#             ft.TextButton("OK", on_click=self.click_book_and_word_ok),
#             ft.TextButton("Cancel", on_click=self.click_book_and_word_cancel),
#         ],
#     )
#     self.page.open(self.get_book_and_word_dialog)
#     self.page.update()

# def click_book_and_word_cancel(self, e: ft.ControlEvent):
#     self.get_book_and_word_dialog.open = False
#     self.page.update()

# def click_book_and_word_ok(self, e: ft.ControlEvent):
#     self.get_book_and_word_dialog.open = False
#     self.page.update()
#     if self.book_input.value and self.word_input.value:
#         self.cst_examples = find_cst_source_sutta_example(
#             self.book_input.value,
#             self.word_input.value,
#         )
#         if self.cst_examples:
#             self.choose_example()
#         else:
#             # self.word_in_text_field.error_text = "not found" # TODO add book and word fields
#             self.ui.update_message("no examples found")
