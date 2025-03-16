import flet as ft
from db_tests.gui.add_family_compound_neg import add_fc_neg
from db_tests.gui.add_family_compound_taddhita import add_fc_taddhita
from db_tests.gui.add_family_compound_su_dur import add_fc_su_dur
from db_tests.gui.add_antonyms import add_antonyms


class TestRunner:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Database Tests"
        self.initial_right_panel_content = ft.Text("Select a test to run", size=20)
        self.right_panel: ft.Container | None = None

    def reset_panel(self):
        """Reset the right panel to initial state"""
        if self.right_panel:
            self.right_panel.content = self.initial_right_panel_content
            self.page.update()


def main(page: ft.Page):
    runner = TestRunner(page)
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    # Test buttons for navigation drawer
    test_buttons = ft.Column(
        controls=[
            ft.Text(""),
            ft.Text(""),
            ft.ListTile(
                title=ft.Text("Add family compounds to negatives"),
                on_click=lambda e: run_test(e, "add_fc_neg"),
            ),
            ft.ListTile(
                title=ft.Text("Add family compounds to taddhita"),
                on_click=lambda e: run_test(e, "add_fc_taddhita"),
            ),
            ft.ListTile(
                title=ft.Text("Add family compounds to su dur sa"),
                on_click=lambda e: run_test(e, "add_fc_su_dur"),
            ),
            ft.ListTile(
                title=ft.Text("Add antonyms"),
                on_click=lambda e: run_test(e, "add_antonyms"),
            ),
        ],
        spacing=10,
    )

    # Navigation Drawer
    page.drawer = ft.NavigationDrawer(
        controls=[test_buttons],
        open=True,
        bgcolor=ft.colors.BLUE_GREY_900,
    )

    # Drawer toggle function
    def toggle_sidemenu(e):
        page.drawer.open = not page.drawer.open
        page.update()

    # AppBar with menu button
    page.appbar = ft.AppBar(
        title=ft.Text("Database Test Runner"),
        center_title=True,
        bgcolor=ft.colors.BLUE_GREY_900,
        leading=ft.IconButton(
            ft.icons.MENU,
            on_click=toggle_sidemenu,
        ),
    )

    # Set window size
    page.window.width = 2048 * 0.67
    page.window.height = 1280
    page.window.top = 0
    page.window.left = 0

    # Function to run a test

    def run_test(e: ft.ControlEvent, test_name: str):
        page.drawer.open = False
        if test_name == "add_fc_neg":
            add_fc_neg(e, page, right_panel)
        elif test_name == "add_fc_taddhita":
            add_fc_taddhita(e, page, right_panel)
        elif test_name == "add_fc_su_dur":
            add_fc_su_dur(e, page, right_panel)
        elif test_name == "add_antonyms":
            add_antonyms(e, page, right_panel)
        runner.reset_panel()
        page.update()

    # Handle Ctrl+Q to quit
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Q" and e.ctrl:
            page.window.close()

    page.on_keyboard_event = on_keyboard

    # Right panel for test results
    right_panel = ft.Container(
        content=runner.initial_right_panel_content,
        expand=True,
        padding=ft.padding.only(left=450, right=100, top=20, bottom=20),
        alignment=ft.alignment.center,
    )

    runner.right_panel = right_panel
    page.add(right_panel)


ft.app(target=main)
