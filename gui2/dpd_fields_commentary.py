import flet as ft
from rich import print

from db.models import BoldDefinition
from gui2.dpd_fields_classes import DpdTextField
from gui2.dpd_fields_functions import clean_commentary
from gui2.flet_functions import process_bold_tags
from tools.bold_definitions_search import BoldDefinitionsSearchManager
from tools.sandhi_contraction import SandhiContractionDict


class DpdCommentaryField(ft.Column):
    def __init__(
        self,
        ui,
        field_name,
        dpd_fields,
        sandhi_dict,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
    ):
        super().__init__(
            width=1200,
            expand=True,
        )

        from gui2.dpd_fields import DpdFields
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass2AddView | Pass1AddView = ui
        self.page: ft.Page = self.ui.page
        self.field_name = field_name
        self.dpd_fields: DpdFields = dpd_fields
        self.sandhi_dict: SandhiContractionDict = sandhi_dict

        self.text_field = DpdTextField(
            multiline=True,
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
        )

        self.search_field_1 = ft.TextField(
            "",
            width=200,
            on_submit=self.click_commentary_search,
            hint_text="search for",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
        )
        self.search_field_2 = ft.TextField(
            "",
            width=200,
            on_submit=self.click_commentary_search,
            hint_text="which contains",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
        )

        self.controls = [
            self.text_field,
            ft.Row(
                [
                    self.search_field_1,
                    self.search_field_2,
                    ft.ElevatedButton("Clear", on_click=self.click_commentary_clear),
                ],
                spacing=0,
            ),
        ]
        self.spacing = 0
        self.commentary_list: list[BoldDefinition] = []
        self.commentary_list_index: str = ""

        @property
        def value(self):
            return self.text_field.value

        @property
        def field(self):
            return self.text_field

        @value.setter
        def value(self, value):
            self.text_field.value = value

    def click_commentary_search(self, e: ft.ControlEvent):
        self.search_field_1.error_text = None

        commentary_searcher = BoldDefinitionsSearchManager()
        if (
            self.search_field_1.value is not None
            and self.search_field_2.value is not None
        ):
            self.commentary_list = commentary_searcher.search(
                self.search_field_1.value, self.search_field_2.value
            )

            if self.commentary_list:
                self.choose_commentary()
            else:
                self.search_field_1.error_text = "not found"
                self.search_field_1.focus()
                self.page.update()

    def choose_commentary(self):
        if not self.commentary_list:
            return

        self.checked_items = []
        example_list = []

        for counter, i in enumerate(self.commentary_list):
            example_list.append(
                ft.Column(
                    [
                        ft.Row(
                            controls=[
                                ft.Checkbox(
                                    width=30,
                                    value=False,
                                    data=counter,
                                    on_change=self.update_checked_items,
                                ),
                                ft.Text(f"{str(counter + 1)}"),
                            ],
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    "",
                                    spans=process_bold_tags(
                                        f"({i.ref_code.strip()}) {i.commentary.strip()}"
                                    ),
                                    expand=True,
                                    selectable=True,
                                )
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    f"{i.nikaya}, {i.book}, {i.title}, {i.subhead}",
                                    size=10,
                                    color=ft.Colors.GREY_500,
                                )
                            ]
                        ),
                    ]
                )
            )

        self.choose_example_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=example_list,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("OK", on_click=self.click_choose_example_ok),
                ft.TextButton("Cancel", on_click=self.click_choose_example_cancel),
            ],
        )

        self.page.open(self.choose_example_dialog)
        self.page.update()

    def update_checked_items(self, e):
        """Track checked/unchecked items"""
        checkbox_value = e.control.value
        item_index = e.control.data
        if checkbox_value and item_index not in self.checked_items:
            self.checked_items.append(item_index)
        elif not checkbox_value and item_index in self.checked_items:
            self.checked_items.remove(item_index)
        print(self.checked_items)

    def click_choose_example_cancel(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

    def click_choose_example_ok(self, e: ft.ControlEvent):
        self.choose_example_dialog.open = False
        self.page.update()

        commentary_list_reduced: list[BoldDefinition] = [
            self.commentary_list[i] for i in self.checked_items
        ]

        commentary_compiled = "\n".join(
            [f"({i.ref_code}) {i.commentary}" for i in commentary_list_reduced]
        )
        commentary_clean = clean_commentary(commentary_compiled, self.sandhi_dict)

        self.text_field.value = commentary_clean
        self.page.update()

    def click_commentary_clear(self, e: ft.ControlEvent):
        self.text_field.value = ""
        self.page.update()
