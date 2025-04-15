import flet as ft

from gui2.pass1 import Pass1View
from gui2.pass1_preprocess_view import Pass1PreProcessView


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        if page.theme is None:
            page.theme = ft.Theme()
        page.theme.font_family = "Inter"
        self.page.window.top = 0
        self.page.window.left = 0
        self.page.window.height = 1280
        self.page.window.width = 1350
        self.page.title = "dpd-db gui"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.build_ui()
        self.page.on_keyboard_event = self.on_keyboard

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

    def build_ui(self) -> None:
        """Constructs the main UI elements."""
        pass1_preprocess_view: Pass1PreProcessView = Pass1PreProcessView(self.page)
        pass1_view: Pass1View = Pass1View(self.page)
        pass2_view_placeholder: ft.Text = ft.Text("Pass2 View - Not Implemented")
        edit_view_placeholder: ft.Text = ft.Text("Edit View - Not Implemented")

        tabs: ft.Tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Pass1 PreProcess",
                    content=pass1_preprocess_view,
                ),
                ft.Tab(
                    text="Pass1",
                    content=pass1_view,
                ),
                ft.Tab(
                    text="Pass2",
                    content=pass2_view_placeholder,
                ),
                ft.Tab(
                    text="Edit",
                    content=edit_view_placeholder,
                ),
            ],
            expand=True,
        )
        self.page.add(tabs)
        self.page.update()


def main(page: ft.Page) -> None:
    App(page)


if __name__ == "__main__":
    ft.app(target=main)
