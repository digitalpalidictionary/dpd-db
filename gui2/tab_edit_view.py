import flet as ft

from gui2.class_database import DatabaseManager
from gui2.class_mixins import PopUpMixin
from gui2.class_dpd_fields import DpdFields

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class EditView(ft.Column, PopUpMixin):
    def __init__(self, page: ft.Page, db: DatabaseManager) -> None:
        # Main container column - does not scroll, expands vertically
        super().__init__(
            expand=True,  # Main column expands
            controls=[],  # Controls defined below
            spacing=5,
            # scroll=None, # Ensure main column doesn't scroll
        )
        self.db = db

        # Placeholder for top fixed section
        self.top_section = ft.Container(
            content=ft.Text("Top Section Placeholder", height=50),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
            # No expand=True here
        )

        # Initialize DPD fields
        self.dpd_fields = DpdFields(self, self.db)

        # Middle scrollable section with all DPD fields
        self.middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO, expand=True, spacing=5
        )

        # Add all fields to the middle section
        # Show all fields in EditView
        self.dpd_fields.add_to_ui(self.middle_section, visible_fields=None)

        # Placeholder for bottom fixed section
        self.bottom_section = ft.Container(
            content=ft.Text("Bottom Section Placeholder"),  # Example content
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
            # No expand=True here
        )

        # Add the sections to the main column's controls list
        self.controls = [
            self.top_section,
            self.middle_section,
            self.bottom_section,
        ]

        # Store page reference if needed
        self.page = page

    # You might add methods later to populate these sections dynamically
    # def update_content(self, data):
    #     self.middle_section.controls = [...]
    #     self.update()

    def build(self):
        # The structure is defined in __init__. Flet calls build automatically.
        # Returning self is standard if __init__ sets up the controls.
        return self
