import flet as ft


def main(page: ft.Page):
    page.title = "Dictionary Entry Field"

    # Create a container with padding
    container = ft.Container(
        padding=20,
        content=ft.Column(
            [
                # Basic text field with character counter
                ft.TextField(
                    label="Pāḷi Word",
                    label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
                    width=400,
                    border_radius=5,
                    border_color="blue",
                    counter_text="{value_length}/{max_length}",
                    max_length=100,
                ),
                # Field for translation with alignment
                ft.TextField(
                    label="Translation",
                    # hint_text="Enter translation",
                    label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
                    width=400,
                    text_align=ft.TextAlign.JUSTIFY,
                    min_lines=3,
                    max_lines=5,
                    multiline=True,
                    helper_text="Provide clear translation",
                ),
            ]
        ),
    )

    page.add(container)
    page.update()


ft.app(target=main)
