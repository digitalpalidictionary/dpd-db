import flet as ft

from gui2.class_database import DatabaseManager
from gui2.class_mixins import PopUpMixin
from gui2.class_dpd_fields import DpdFields
from gui2.class_pass2_file_manager import Pass2AutoFileManager

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

        # Initialize Pass2 manager
        self.pass2_manager = Pass2AutoFileManager()

        # Top section with Pass2 navigation
        self.pass2_label = ft.Text("Current Pass2: None", expand=True)
        self.next_button = ft.ElevatedButton(
            "Next Pass2 Entry", width=BUTTON_WIDTH, on_click=self._load_next_pass2_entry
        )

        self.top_section = ft.Container(
            content=ft.Row(
                controls=[self.pass2_label, self.next_button],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
            # No expand=True here
        )

        # Initialize single DPD fields instance
        self.dpd_fields = DpdFields(self, self.db)

        # Middle section is a single scrolling column
        self.middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO, expand=True, spacing=5
        )

        # Add all fields with add fields included (for Pass2 editing)
        self.dpd_fields.add_to_ui(self.middle_section, include_add_fields=True)

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

    def _load_next_pass2_entry(self, e: ft.ControlEvent | None = None) -> None:
        """Load next pass2 entry into the view."""
        headword_id, data = self.pass2_manager.get_next_headword_data()

        if headword_id is not None:
            self.pass2_label.value = (
                f"Current Pass2: {data.get('pali_1', headword_id)} (ID: {headword_id})"
            )
            self.dpd_fields.update_fields(data, target="add")  # Update add fields
            self.dpd_fields.clear_fields(target="main")  # Clear main fields
        else:
            self.pass2_label.value = "Current Pass2: None"
            self.dpd_fields.clear_fields(target="all")  # Clear all fields

        self.update()

    def build(self):
        # The structure is defined in __init__. Flet calls build automatically.
        # Returning self is standard if __init__ sets up the controls.
        return self
