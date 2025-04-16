from tools.paths import ProjectPaths
import flet as ft


class SandhiOK:
    """Requires pth = ProjectPaths()"""

    pth = ProjectPaths()

    def update_sandhi_ok(self, sandhi: str, breakup: str):
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


class PopUpMixin:
    def __init__(self):
        self._popup_textfield = ft.TextField(
            label="Enter value",
            autofocus=True,
            width=1000,
        )
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("What's the construction?"),
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
        page.add(self._dialog)
        self._dialog.open = True
        page.update()
