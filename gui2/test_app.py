import flet as ft

from gui2.filter_tab_view import (
    FilterTabView,
)
from gui2.tests_tab_view import (
    TestsTabView,
)
from gui2.toolkit import ToolKit


def main(page: ft.Page):
    page.title = "Flet Test App for DB Tests Tab"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.ADAPTIVE

    # Set window dimensions to match main.py
    page.window.top = 0
    page.window.left = 0
    page.window.height = 1280
    page.window.width = 1375

    toolkit = ToolKit(page)

    # Create tabs for both Tests and Filter functionality
    tests_tab_view = TestsTabView(page, toolkit)
    filter_tab_view = FilterTabView(
        page,
        toolkit,
        data_filters=[("root_key", ""), ("family_root", "")],
        display_filters=["id", "lemma_1", "meaning_1", "meaning_lit"],
        limit=0,
    )

    # Create tabs
    tabs = ft.Tabs(
        content=ft.Column(
            [
                ft.TabBar(tabs=[ft.Tab(label="√"), ft.Tab(label="Tests")]),
                ft.TabBarView(
                    controls=[filter_tab_view, tests_tab_view],
                    expand=True,
                ),
            ],
            expand=True,
        ),
        length=2,
        selected_index=0,
        animation_duration=300,
        expand=True,
    )

    page.add(tabs)


if __name__ == "__main__":
    ft.run(main)
