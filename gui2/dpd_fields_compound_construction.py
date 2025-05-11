import flet as ft
import re

from gui2.dpd_fields_classes import DpdTextField
from gui2.dpd_fields_functions import make_compound_construction_from_headword


class DpdCompoundConstructionField(ft.Column):
    def __init__(
        self,
        ui,
        field_name,
        dpd_fields,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
    ):
        super().__init__(
            expand=True,
            spacing=0,
        )

        from gui2.dpd_fields import DpdFields
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass2AddView | Pass1AddView = ui
        self.page: ft.Page = self.ui.page
        self.field_name = field_name
        self.dpd_fields: DpdFields = dpd_fields

        self.compound_construction_field = DpdTextField(
            name=field_name,
            multiline=False,
            on_focus=self.compound_construction_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
        )

        self.bolding_field = ft.TextField(
            label="Bold",
            label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
            dense=True,
            text_size=12,
            on_submit=self._handle_bolding_submit,
        )

        self.controls = [
            self.compound_construction_field,
            self.bolding_field,
        ]

    @property
    def value(self):
        return self.compound_construction_field.value

    @property
    def field(self):
        return self.compound_construction_field

    @value.setter
    def value(self, value):
        self.compound_construction_field.value = value

    @property
    def error_text(self):
        """Gets the error text from the internal compound construction field."""
        return self.compound_construction_field.error_text

    @error_text.setter
    def error_text(self, value):
        """Sets the error text on the internal compound construction field and updates it."""
        self.compound_construction_field.error_text = value
        self.compound_construction_field.update()

    def _handle_bolding_submit(self, e: ft.ControlEvent):
        bold_text = e.control.value
        current_value = self.compound_construction_field.value
        if bold_text and current_value and bold_text in current_value:
            new_value = re.sub(
                re.escape(bold_text), f"<b>{bold_text}</b>", current_value, count=1
            )
            self.compound_construction_field.value = new_value
            e.control.value = ""
            self.page.update()
            self.compound_construction_field.focus()

    def compound_construction_focus(self, e: ft.ControlEvent) -> None:
        """Autofill compound_construction."""

        compound_construction_field = e.control
        compound_construction_value = e.control.value
        compound_type_field = self.dpd_fields.get_field("compound_type")
        compound_type_value = compound_type_field.value

        if compound_type_value and not compound_construction_value:
            current_headword = self.dpd_fields.get_current_headword()
            cc = make_compound_construction_from_headword(current_headword)
            compound_construction_field.value = cc

        compound_construction_field.focus()
        self.page.update()
