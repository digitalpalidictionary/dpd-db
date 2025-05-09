import flet as ft
from tools.printer import printer as pr  # For logging/debugging


class AiSearchPopup:
    def __init__(self, toolkit):
        from gui2.toolkit import ToolKit

        self.toolkit: ToolKit = toolkit
        self.page: ft.Page = toolkit.page
        self.ai_manager = toolkit.ai_manager

        # Initialize UI components
        self.prompt_field = ft.TextField(
            expand=True,
            autofocus=True,
            on_submit=self._handle_submit,
            border_radius=20,
            border=None,
        )
        self.response_field = ft.Markdown(
            "",
            selectable=True,
            expand=True,
            auto_follow_links=True,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                [
                    ft.Row([ft.Text("Ask AI", size=14, color=ft.Colors.GREY_500)]),
                    ft.Row([self.prompt_field]),
                    ft.Container(
                        ft.Column(
                            [self.response_field],
                            expand=True,
                            scroll=ft.ScrollMode.AUTO,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                        ),
                        border_radius=20,
                        expand=True,
                        padding=20,
                        width=1000,
                    ),
                ],
                width=1000,
                height=1000,
            ),
            actions=[
                ft.TextButton("Close", on_click=self._handle_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _handle_submit(self, e: ft.ControlEvent):
        prompt_text = self.prompt_field.value
        if not prompt_text:
            self.prompt_field.error_text = "Please enter a prompt."
            self.page.update()
            return

        self.response_field.value = "Getting response..."
        self.dialog.update()

        try:
            response = self.ai_manager.request(prompt=prompt_text, grounding=True)
            if response:
                self.response_field.value = response
            else:
                self.response_field.value = "AI request failed or returned no response."
        except Exception as ex:
            pr.error(f"AI request error in popup: {ex}")
            self.response_field.value = f"An error occurred: {ex}"
        finally:
            self.page.update()

    def _handle_close(self, e: ft.ControlEvent | None):
        self.dialog.open = False
        self.page.update()

    def open_popup(self):
        self.prompt_field.value = ""
        self.response_field.value = ""
        self.page.open(self.dialog)
        self.page.update()

    def is_dialog_open(self) -> bool:
        return self.dialog.open

    def close_dialog(self) -> None:
        if self.is_dialog_open():
            self._handle_close(None)
