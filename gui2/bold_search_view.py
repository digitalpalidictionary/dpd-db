import re

import flet as ft

from gui2.bold_search_controller import BoldSearchController
from gui2.toolkit import ToolKit

LABEL_WIDTH = 250
COLUMN_WIDTH: int = 700
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
TEXT_FIELD_LABEL_STYLE = ft.TextStyle(color=LABEL_COLOUR, size=10)


def parse_html_bold(text: str) -> list[ft.TextSpan]:
    """Parses a string with <b> tags into a list of Flet TextSpans."""
    spans = []
    # Split by <b> and </b> tags, keeping the delimiters
    parts = re.split(r"(<b>|</b>)", text)
    is_bold = False
    for part in parts:
        if part == "<b>":
            is_bold = True
        elif part == "</b>":
            is_bold = False
        elif part:  # Don't add empty strings
            weight = ft.FontWeight.BOLD if is_bold else ft.FontWeight.NORMAL
            spans.append(ft.TextSpan(part, ft.TextStyle(weight=weight)))
    return spans


class BoldSearchView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit
        self.controller = BoldSearchController(
            self,
            toolkit,
        )

        # Define controls
        self.search_bold_field = ft.TextField(
            "",
            expand=True,
            label="Search Bold",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=ft.Colors.WHITE,
            border_radius=20,
            autofocus=True,
            on_submit=self.controller.perform_search,
        )

        self.search_within_field = ft.TextField(
            "",
            expand=True,
            label="Search Within",
            label_style=TEXT_FIELD_LABEL_STYLE,
            color=ft.Colors.WHITE,
            border_radius=20,
            on_submit=self.controller.perform_search,
        )

        self.results_search_field = ft.TextField(
            label="Search in results",
            label_style=TEXT_FIELD_LABEL_STYLE,
            width=300,
            on_change=self.handle_text_search,
            border_radius=20,
            border_color=HIGHLIGHT_COLOUR,
        )

        self.results_pane = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=True,
        )

        self.results_display_container = ft.Container(
            content=self.results_pane,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            expand=True,
            visible=False,  # Initially hidden
        )

        self.controls.extend(
            [
                ft.Container(
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    self.search_bold_field,
                                    self.search_within_field,
                                ],
                            ),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Search",
                                        on_click=self.controller.perform_search,
                                    ),
                                    ft.ElevatedButton(
                                        "Clear",
                                        on_click=self.controller.clear_fields,
                                    ),
                                    self.results_search_field,
                                ],
                            ),
                            ft.Divider(),
                            ft.Row(
                                expand=True,
                                controls=[
                                    self.results_display_container,
                                ],
                            ),
                        ]
                    ),
                    border_radius=20,
                    padding=ft.Padding(0, 10, 0, 0),
                )
            ]
        )

    def update_results(self, results: list, search_within: str):
        self.results_pane.controls.clear()
        if not results:
            self.results_pane.controls.append(ft.Text("No results found."))
            self.results_display_container.visible = (
                False  # Hide container if no results
            )
        else:
            self.results_display_container.visible = True  # Show container if results
            for i, r in enumerate(results):
                # --- Left Cell ---
                index_span = ft.TextSpan(
                    f"{i + 1}. ", ft.TextStyle(weight=ft.FontWeight.BOLD)
                )
                bold_spans = parse_html_bold(r.bold)
                left_cell_spans = [index_span] + bold_spans
                left_text_widget = ft.Text(spans=left_cell_spans, selectable=True)
                left_text_widget.data = left_cell_spans  # Store original spans

                # --- Right Cell ---
                commentary_spans = []
                if search_within:
                    parts = re.split(
                        f"""({re.escape(search_within)})""",
                        r.commentary,
                        flags=re.IGNORECASE,
                    )
                    for part in parts:
                        sub_spans = parse_html_bold(part)
                        if part.lower() == search_within.lower():
                            for span in sub_spans:
                                existing_style = (
                                    span.style if span.style else ft.TextStyle()
                                )
                                span.style = ft.TextStyle(
                                    size=existing_style.size,
                                    weight=existing_style.weight,
                                    italic=existing_style.italic,
                                    font_family=existing_style.font_family,
                                    decoration=existing_style.decoration,
                                    decoration_color=existing_style.decoration_color,
                                    decoration_style=existing_style.decoration_style,
                                    height=existing_style.height,
                                    word_spacing=existing_style.word_spacing,
                                    letter_spacing=existing_style.letter_spacing,
                                    baseline=existing_style.baseline,
                                    overflow=existing_style.overflow,
                                    shadow=existing_style.shadow,
                                    foreground=existing_style.foreground,
                                    color=ft.Colors.BLACK,
                                    bgcolor=ft.Colors.YELLOW_200,
                                )
                        commentary_spans.extend(sub_spans)
                else:
                    commentary_spans = parse_html_bold(r.commentary)

                commentary_text_widget = ft.Text(
                    spans=[
                        ft.TextSpan(f"({r.ref_code}) "),
                        *commentary_spans,
                    ],
                    selectable=True,
                )
                commentary_text_widget.data = (
                    commentary_text_widget.spans
                )  # Store original spans

                metadata_text_widget = ft.Text(
                    f"{r.nikaya}, {r.book}, {r.title}, {r.subhead}",
                    color=ft.Colors.GREY_600,
                    size=12,
                    selectable=True,
                )
                metadata_text_widget.data = [
                    ft.TextSpan(
                        metadata_text_widget.value, style=metadata_text_widget.style
                    )
                ]  # Store as list of spans

                right_cell = ft.Column(
                    expand=True,
                    controls=[
                        commentary_text_widget,
                        metadata_text_widget,
                    ],
                )

                # --- Main Row ---
                result_row = ft.Row(
                    controls=[
                        ft.Container(
                            content=left_text_widget,
                            width=300,
                            alignment=ft.alignment.top_left,
                        ),
                        ft.Container(
                            content=right_cell,
                            expand=True,
                            alignment=ft.alignment.top_left,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )

                self.results_pane.controls.append(result_row)
                self.results_pane.controls.append(
                    ft.Divider(height=1, color=ft.Colors.GREY_300)
                )

        self.page.update()

    def clear_all_fields(self):
        self.search_bold_field.value = ""
        self.search_within_field.value = ""
        self.results_search_field.value = ""
        self.results_pane.controls.clear()
        self.results_display_container.visible = False  # Hide container on clear
        self.page.update()

    def handle_text_search(self, e: ft.ControlEvent):
        query = (e.data or "").lower()

        for control in self.results_pane.controls:
            if not isinstance(control, ft.Row):  # Skip Dividers
                continue

            result_row = control  # This is the ft.Row for one result
            found_in_card = False

            # Access left_cell and right_cell containers
            left_container_control = result_row.controls[0]
            right_container_control = result_row.controls[1]

            if not isinstance(left_container_control, ft.Container) or not isinstance(
                right_container_control, ft.Container
            ):
                continue

            left_container: ft.Container = left_container_control
            right_container: ft.Container = right_container_control

            # Access ft.Text controls within them
            left_text_control = left_container.content
            if not isinstance(left_text_control, ft.Text):
                continue
            left_text_widget: ft.Text = left_text_control

            right_column_control = right_container.content
            if not isinstance(right_column_control, ft.Column):
                continue
            right_column_content: ft.Column = right_column_control

            commentary_text_control = right_column_content.controls[0]
            metadata_text_control = right_column_content.controls[1]

            if not isinstance(commentary_text_control, ft.Text) or not isinstance(
                metadata_text_control, ft.Text
            ):
                continue

            commentary_text_widget: ft.Text = commentary_text_control
            metadata_text_widget: ft.Text = metadata_text_control

            # Process left_text_widget (index + bold)
            if hasattr(left_text_widget, "data") and left_text_widget.data:
                original_spans = left_text_widget.data
                if query:
                    new_spans, found = self._create_highlighted_spans(
                        original_spans, query
                    )
                    left_text_widget.spans = new_spans
                    if found:
                        found_in_card = True
                else:
                    left_text_widget.spans = original_spans

            # Process commentary_text_widget
            if hasattr(commentary_text_widget, "data") and commentary_text_widget.data:
                original_spans = commentary_text_widget.data
                if query:
                    new_spans, found = self._create_highlighted_spans(
                        original_spans, query
                    )
                    commentary_text_widget.spans = new_spans
                    if found:
                        found_in_card = True
                else:
                    commentary_text_widget.spans = original_spans

            # Process metadata_text_widget
            if hasattr(metadata_text_widget, "data") and metadata_text_widget.data:
                original_spans = metadata_text_widget.data
                if query:
                    new_spans, found = self._create_highlighted_spans(
                        original_spans, query
                    )
                    metadata_text_widget.spans = new_spans
                    if found:
                        found_in_card = True
                else:
                    metadata_text_widget.spans = original_spans

            # Apply/remove border to the result_row's containers
            if query and found_in_card:
                left_container.border = ft.border.all(2, HIGHLIGHT_COLOUR)
                left_container.border_radius = 10
                left_container.padding = 10
                right_container.border = ft.border.all(2, HIGHLIGHT_COLOUR)
                right_container.border_radius = 10
                right_container.padding = 10
            else:
                left_container.border = None
                left_container.border_radius = None
                left_container.padding = None
                right_container.border = None
                right_container.border_radius = None
                right_container.padding = None

        self.page.update()

    def _create_highlighted_spans(
        self,
        spans: list[ft.TextSpan],
        query: str,
    ) -> tuple[list[ft.TextSpan], bool]:
        new_spans = []
        found_match = False

        for span in spans:
            if not isinstance(span, ft.TextSpan) or not span.text:
                new_spans.append(span)
                continue

            text = span.text
            parts = re.split(f"({re.escape(query)})", text, flags=re.IGNORECASE)

            if len(parts) > 1:
                found_match = True
                for i, part in enumerate(parts):
                    if not part:
                        continue
                    if i % 2 == 1:  # the matched part
                        existing_style = span.style if span.style else ft.TextStyle()

                        new_style = ft.TextStyle(
                            size=existing_style.size,
                            weight=existing_style.weight,
                            italic=existing_style.italic,
                            font_family=existing_style.font_family,
                            decoration=existing_style.decoration,
                            decoration_color=existing_style.decoration_color,
                            decoration_style=existing_style.decoration_style,
                            height=existing_style.height,
                            word_spacing=existing_style.word_spacing,
                            letter_spacing=existing_style.letter_spacing,
                            baseline=existing_style.baseline,
                            overflow=existing_style.overflow,
                            shadow=existing_style.shadow,
                            foreground=existing_style.foreground,
                            color=ft.Colors.BLACK,
                            bgcolor=HIGHLIGHT_COLOUR,
                        )
                        new_spans.append(ft.TextSpan(part, style=new_style))
                    else:  # the parts not matching
                        new_spans.append(ft.TextSpan(part, style=span.style))
            else:
                new_spans.append(span)

        return new_spans, found_match
