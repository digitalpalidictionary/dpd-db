import flet as ft

from gui2.filter_component import FilterComponent
from gui2.toolkit import ToolKit


class FilterTabView(ft.Column):
    """Filter tab for database filtering functionality."""

    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        # Create and add the filter component
        self.filter_component = FilterComponent(self.page, self.toolkit)

        # Build UI structure
        self.controls.extend(
            [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Database Filter",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            self.filter_component,
                        ]
                    ),
                    padding=10,
                )
            ]
        )
