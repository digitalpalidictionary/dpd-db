import flet as ft

from db_tests.gui.add_antonyms import add_antonyms
from db_tests.gui.add_antonyms_sync import add_antonyms_sync
from db_tests.gui.add_family_compound_neg import add_fc_neg
from db_tests.gui.add_family_compound_su_dur import add_fc_su_dur
from db_tests.gui.add_family_compound_taddhita import add_fc_taddhita


class TestRunner:
    def __init__(self, page: ft.Page):
        self.page = page
        # self.page.title = "Database Tests"
        self.initial_right_panel_content = ft.Text("Select a test to run", size=20)
        self.right_panel: ft.Container | None = None
        self.running_test = False

    def reset_panel(self):
        """Reset the right panel to initial state"""
        if self.right_panel:
            # self.page.appbar.title = ft.Text("")
            self.right_panel.content = self.initial_right_panel_content
            self.page.update()


def main(page: ft.Page):
    runner = TestRunner(page)
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    # page.window.title_bar_hidden = True  # Hide native title bar
    # page.window.title_bar_buttons_hidden = True  # Hide minimize/maximize/close

    # AppBar with menu button (CREATE THIS FIRST)
    page.appbar = ft.AppBar(
        title=ft.Text("Database Test Runner"),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
        elevation=0,
        leading=ft.IconButton(
            ft.Icons.MENU,
        ),
    )

    # Set window size
    page.window.width = 2048 * 0.67
    page.window.height = 1280
    page.window.top = 0
    page.window.left = 0

    # Test buttons for side panel
    test_buttons = ft.Column(
        controls=[
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
            ft.ListTile(
                title=ft.Text("Add antonyms sync"),
                on_click=lambda e: run_test(e, "add_antonyms sync"),
            ),
        ],
        spacing=10,
    )

    # Side panel (Container)
    side_panel = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text("Tests", size=18, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.only(top=40, bottom=20, left=16),
                ),
                ft.Divider(height=1),
                test_buttons,
            ],
            tight=True,
        ),
        width=500,
        left=-500,
        top=0,
        bottom=0,
        padding=ft.padding.only(left=10),
        animate=ft.animation.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
    )

    # Drawer toggle function
    def toggle_sidemenu(e):
        side_panel.left = 0 if side_panel.left == -500 else -500
        page.update()

    # add the toggle function to the appbar
    page.appbar.leading.on_click = toggle_sidemenu

    # Function to run a test
    def run_test(e: ft.ControlEvent, test_name: str):
        if runner.running_test:
            return
        runner.running_test = True
        toggle_sidemenu(e)
        page.appbar.title = ft.Text(e.control.title.value)
        if test_name == "add_fc_neg":
            add_fc_neg(e, page, right_panel)
        elif test_name == "add_fc_taddhita":
            add_fc_taddhita(e, page, right_panel)
        elif test_name == "add_fc_su_dur":
            add_fc_su_dur(e, page, right_panel)
        elif test_name == "add_antonyms":
            add_antonyms(e, page, right_panel)
        elif test_name == "add_antonyms sync":
            add_antonyms_sync(e, page, right_panel)
        runner.reset_panel()
        runner.running_test = False
        page.update()

    # Handle Ctrl+Q to quit
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Q" and e.ctrl:
            if runner.running_test:
                return
            page.window.close()

        if e.key == "S" and e.ctrl:
            page.show_semantics_debugger = not page.show_semantics_debugger
            page.update()

    page.on_keyboard_event = on_keyboard

    # Right panel for test results
    right_panel = ft.Container(
        content=runner.initial_right_panel_content,
        expand=True,
        padding=ft.padding.only(left=100, right=100, top=20, bottom=20),
        alignment=ft.alignment.center,  # This is the key to centering
    )

    runner.right_panel = right_panel

    page.add(right_panel)
    page.overlay.append(side_panel)


ft.app(target=main)
