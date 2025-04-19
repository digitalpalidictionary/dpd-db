import flet as ft
from gui2.class_daily_log import DailyLog
from gui2.class_database import DatabaseManager
from tools.fast_api_utils import start_dpd_server


class App:
    def __init__(self, page: ft.Page):
        from gui2.tab_edit_view import EditView
        from gui2.tab_pass1_view import Pass1View
        from gui2.tab_pass1preprocess_view import Pass1PreProcessView

        self.page = page

        if page.theme is None:
            page.theme = ft.Theme()
        page.theme.font_family = "Inter"
        self.page.window.top = 0
        self.page.window.left = 0
        self.page.window.height = 1280
        self.page.window.width = 1380
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.on_keyboard_event = self.on_keyboard

        self.daily_log = DailyLog()

        page.appbar = ft.AppBar(
            title=ft.Text("dpd gui"),
            bgcolor=ft.Colors.LIGHT_BLUE_900,
            elevation=100,
            title_spacing=20,
            center_title=False,
            actions=[ft.Text(self.daily_log.get_counts())],
        )

        # initilize classes
        self.db = DatabaseManager()
        self.pass1_preprocess_view: Pass1PreProcessView = Pass1PreProcessView(
            self.page, self.db
        )
        self.pass1_view: Pass1View = Pass1View(self.page, self.db)
        self.pass2_view_placeholder: ft.Text = ft.Text("")
        self.edit_view: EditView = EditView(self.page, self.db)

        self.build_ui()

    def on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handles global keyboard events."""
        if e.key == "Q" and e.ctrl:
            self.page.window.close()

    def tab_clicked(self, e: ft.ControlEvent) -> None:
        """Handles tab clicks."""

        # load pass_1 database
        if self.db.all_lemma_1 is None:
            self.db.initialize_db()

    def build_ui(self) -> None:
        """Constructs the main UI elements."""

        tabs: ft.Tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            on_click=self.tab_clicked,
            tabs=[
                ft.Tab(
                    text="Pass1 PreProcess",
                    content=self.pass1_preprocess_view,
                ),
                ft.Tab(
                    text="Pass1",
                    content=self.pass1_view,
                ),
                ft.Tab(
                    text="Pass2",
                    content=self.pass2_view_placeholder,
                ),
                ft.Tab(
                    text="Edit",
                    content=self.edit_view,
                ),
            ],
            expand=True,
        )
        self.page.add(tabs)
        self.page.update()


def main(page: ft.Page) -> None:
    start_dpd_server()
    App(page)


if __name__ == "__main__":
    ft.app(target=main)
