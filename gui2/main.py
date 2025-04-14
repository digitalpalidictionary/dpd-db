import flet as ft

from gui2.pass1 import Pass1View
from gui2.pass1_preprocess import Pass1PreProcessView


class MenuBarHandler:
    def __init__(self, page: ft.Page, main_content_area: ft.Column):
        self.page = page
        self.main_content_area = main_content_area

    def handle_menu_item_click(self, e: ft.ControlEvent) -> None:
        """Handles clicks on menu items."""

        item_text: str = e.control.content.value
        # self.page.open(ft.SnackBar(content=ft.Text(f"{item_text} was clicked!")))

        # Load Views
        if item_text == "Pass1 PreProcess":
            self.main_content_area.controls.clear()
            self.main_content_area.controls.append(Pass1PreProcessView(self.page))
        elif item_text == "Pass1":
            self.main_content_area.controls.clear()
            self.main_content_area.controls.append(Pass1View(self.page))

        self.page.update()


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

        self.main_content_area = ft.Column(expand=True)

        self.menu_handler = MenuBarHandler(
            page=self.page, main_content_area=self.main_content_area
        )

        self.page.on_keyboard_event = self.on_keyboard
        self.build_ui()

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

    def build_ui(self) -> None:
        """Constructs the main UI elements."""
        menubar = ft.MenuBar(
            expand=True,
            style=ft.MenuStyle(
                alignment=ft.alignment.top_left,
                mouse_cursor={
                    ft.ControlState.HOVERED: ft.MouseCursor.WAIT,
                    ft.ControlState.DEFAULT: ft.MouseCursor.ZOOM_OUT,
                },
            ),
            controls=[
                ft.SubmenuButton(
                    content=ft.Text("Apps"),
                    controls=[
                        ft.MenuItemButton(
                            content=ft.Text("Pass1 PreProcess"),
                            style=ft.ButtonStyle(
                                bgcolor={ft.ControlState.HOVERED: ft.Colors.BLUE_500}
                            ),
                            on_click=self.menu_handler.handle_menu_item_click,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Pass1"),
                            style=ft.ButtonStyle(
                                bgcolor={ft.ControlState.HOVERED: ft.Colors.BLUE_500}
                            ),
                            on_click=self.menu_handler.handle_menu_item_click,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Pass2"),
                            style=ft.ButtonStyle(
                                bgcolor={ft.ControlState.HOVERED: ft.Colors.BLUE_500}
                            ),
                            on_click=self.menu_handler.handle_menu_item_click,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Edit"),
                            style=ft.ButtonStyle(
                                bgcolor={ft.ControlState.HOVERED: ft.Colors.BLUE_500}
                            ),
                            on_click=self.menu_handler.handle_menu_item_click,
                        ),
                    ],
                ),
            ],
        )

        # Add the main_content_area to the page layout
        self.page.add(
            ft.Column(
                [
                    ft.Row([menubar]),
                    self.main_content_area,  # Add the content area here
                ],
                expand=True,
            )
        )
        self.page.update()


def main(page: ft.Page) -> None:
    App(page)


if __name__ == "__main__":
    ft.app(target=main)
