import subprocess
import sys
from pathlib import Path

import flet as ft

from tools.ai_manager import AIManager
from tools.printer import printer as pr
from tools.server_mode import is_headless_server

GROUNDED_KEY_PREFIX = "grounded|"
DEFAULT_MODEL_KEY = "grounded|gemini|gemini-2.5-flash"

_process: subprocess.Popen | None = None


def launch_ai_search_window() -> None:
    # Ask AI runs in its own OS window (its own Flet process) so it never
    # blocks the main window and can be alt-tabbed. This is desktop-only: a
    # headless server session has no display to open the native window, so skip
    # it (a web-native in-page Ask AI is future work). Contributors reach this
    # via a keyboard shortcut only, which browsers intercept anyway.
    if is_headless_server():
        return
    # Guard against spawning duplicates: if one is already alive, leave it and
    # let the user switch to it rather than opening a second copy.
    global _process
    if _process is not None and _process.poll() is None:
        return
    _process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve())],
        cwd=str(Path(__file__).resolve().parents[1]),
    )


class AiSearchWindow:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.ai_manager = AIManager()

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

    def build(self) -> ft.Control:
        return ft.Column(
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
                ),
            ],
            expand=True,
        )

    def _build_model_options(self) -> list[ft.dropdown.Option]:
        grounded = [
            ft.dropdown.Option(
                key=f"{GROUNDED_KEY_PREFIX}{provider}|{model_name}",
                text=f"{provider}: {model_name} [web search]",
            )
            for provider, model_name, _delay, _timeout in self.ai_manager.GROUNDED_MODELS
        ]
        standard = [
            ft.dropdown.Option(
                key=f"{provider}|{model_name}", text=f"{provider}: {model_name}"
            )
            for provider, model_name, _delay, _timeout in self.ai_manager.DEFAULT_MODELS
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
        self.page.update()

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
        except Exception as ex:  # noqa: BLE001
            pr.red(f"AI request error in window: {ex}")
            self.response_field.value = f"An error occurred: {ex}"
        finally:
            self.page.update()


def main(page: ft.Page) -> None:
    page.title = "Ask AI"
    page.theme = ft.Theme()
    page.theme.font_family = "Inter"
    page.window.width = 900
    page.window.height = 1000

    window = AiSearchWindow(page)

    def on_keyboard(e: ft.KeyboardEvent) -> None:
        if (e.key == "W" and e.ctrl) or e.key == "Escape":
            page.window.close()

    page.on_keyboard_event = on_keyboard
    page.add(window.build())
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
