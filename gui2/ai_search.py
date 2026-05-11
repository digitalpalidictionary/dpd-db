# -*- coding: utf-8 -*-
import flet as ft

from tools.printer import printer as pr

GROUNDED_KEY_PREFIX = "grounded|"
DEFAULT_MODEL_KEY = "grounded|gemini|gemini-2.5-flash"


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
        self.model_dropdown = ft.Dropdown(
            label="Model",
            options=self._build_model_options(),
            value=DEFAULT_MODEL_KEY,
            expand=True,
            text_size=12,
            border_radius=20,
            border=None,
            on_focus=self._on_model_dropdown_focus,
        )
        self.reload_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Reload AI models and reset to grounded web search",
            on_click=self._on_reload_models,
        )
        self.response_field = ft.Markdown(
            "",
            selectable=True,
            expand=True,
            auto_follow_links=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                [
                    ft.Row([ft.Text("Ask AI", size=14, color=ft.Colors.GREY_500)]),
                    ft.Row([self.prompt_field]),
                    ft.Row([self.model_dropdown, self.reload_button]),
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

    def _build_model_options(self) -> list[ft.dropdown.Option]:
        grounded = [
            ft.dropdown.Option(
                key=f"{GROUNDED_KEY_PREFIX}{provider}|{model_name}",
                text=f"{provider}: {model_name} [web search]",
            )
            for provider, model_name, _delay in self.ai_manager.GROUNDED_MODELS
        ]
        standard = [
            ft.dropdown.Option(
                key=f"{provider}|{model_name}", text=f"{provider}: {model_name}"
            )
            for provider, model_name, _delay in self.ai_manager.DEFAULT_MODELS
        ]
        return grounded + standard

    def _on_model_dropdown_focus(self, e) -> None:
        self.ai_manager.reload_models()
        self.model_dropdown.options = self._build_model_options()
        self.model_dropdown.update()

    def _on_reload_models(self, e) -> None:
        self.ai_manager.reload_models()
        self.model_dropdown.options = self._build_model_options()
        self.model_dropdown.value = DEFAULT_MODEL_KEY
        self.model_dropdown.update()

    def _handle_submit(self, e: ft.ControlEvent):
        prompt_text = self.prompt_field.value
        if not prompt_text:
            self.prompt_field.error_text = "Please enter a prompt."
            self.page.update()
            return

        self.response_field.value = "Getting response..."
        self.dialog.update()

        try:
            selected = self.model_dropdown.value or DEFAULT_MODEL_KEY
            if selected.startswith(GROUNDED_KEY_PREFIX):
                ai_response = self.ai_manager.request(
                    prompt=prompt_text, grounding=True
                )
            else:
                provider_preference, model_name = selected.split("|", 1)
                ai_response = self.ai_manager.request(
                    prompt=prompt_text,
                    provider_preference=provider_preference,
                    model=model_name,
                )

            if ai_response.content:
                self.response_field.value = ai_response.content
            else:
                self.response_field.value = f"AI request failed or returned no response. Status: {ai_response.status_message}"
        except Exception as ex:
            pr.red(f"AI request error in popup: {ex}")
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
