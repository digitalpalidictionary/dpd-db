import flet as ft
from db_tests.gui.add_family_compound_neg import add_fc_neg
from db_tests.gui.add_family_compound_taddhita import add_fc_taddhita
from db_tests.gui.add_family_compound_su_dur import add_fc_su_dur


class TestRunner:
    def __init__(self, page: ft.Page):
        self.page = page
        self.initial_right_panel_content = ft.Text("Select a test to run", size=20)
        self.right_panel: ft.Container | None = None

    def reset_panel(self):
        """Reset the right panel to initial state"""
        if self.right_panel:
            self.right_panel.content = self.initial_right_panel_content
            self.page.update()


def main(page: ft.Page):
    runner = TestRunner(page)
    page.title = "Database Test Runner"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    def run_test(e: ft.ControlEvent, test_name: str):
        if test_name == "add_fc_neg":
            add_fc_neg(page, right_panel)
        elif test_name == "add_fc_taddhita":
            add_fc_taddhita(page, right_panel)
        elif test_name == "add_fc_su_dur":
            add_fc_su_dur(page, right_panel)
        runner.reset_panel()

    # Left panel with test buttons
    test_buttons = ft.Column(
        controls=[
            ft.TextButton(
                text="Add family compounds to negatives",
                width=500,
                on_click=lambda e: run_test(e, "add_fc_neg"),
            ),
            ft.TextButton(
                text="Add family compounds to taddhita",
                width=500,
                on_click=lambda e: run_test(e, "add_fc_taddhita"),
            ),
            ft.TextButton(
                text="Add family compounds to su dur sa",
                width=500,
                on_click=lambda e: run_test(e, "add_fc_su_dur"),
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        spacing=10,
    )

    # Handle Ctrl+Q to quit
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Q" and e.ctrl:
            page.window.close()

    page.on_keyboard_event = on_keyboard

    left_panel = ft.Container(
        content=test_buttons,
        padding=0,
        bgcolor=ft.Colors.BLUE_GREY_900,
        alignment=ft.alignment.bottom_right,
    )

    # Right panel for test results
    right_panel = ft.Container(
        content=runner.initial_right_panel_content,
        width=page.window.width * 0.66 if page.window.width else 800,
        padding=20,
        alignment=ft.alignment.top_left,
    )

    # Main row to hold both panels
    main_row = ft.Row(
        controls=[left_panel, right_panel],
        spacing=0,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    runner.right_panel = right_panel
    page.add(main_row)


ft.app(target=main)
