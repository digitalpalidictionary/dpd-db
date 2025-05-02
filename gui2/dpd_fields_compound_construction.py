import flet as ft
import re

from gui2.dpd_fields_classes import DpdTextField


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
            spacing=0,  # Keep spacing tight
        )

        from gui2.dpd_fields import DpdFields
        from gui2.pass1_add_view import Pass1AddView
        from gui2.pass2_add_view import Pass2AddView

        self.ui: Pass2AddView | Pass1AddView = ui
        self.page: ft.Page = self.ui.page
        self.field_name = field_name
        self.dpd_fields: DpdFields = dpd_fields

        self.text_field = DpdTextField(
            name=field_name,
            multiline=False,  # Compound constructions are usually single line
            on_focus=on_focus,
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
            self.text_field,
            self.bolding_field,
        ]

    @property
    def value(self):
        return self.text_field.value

    @property
    def field(self):
        return self.text_field

    @value.setter
    def value(self, value):
        self.text_field.value = value

    def _handle_bolding_submit(self, e: ft.ControlEvent):
        bold_text = e.control.value
        current_value = self.text_field.value
        if bold_text and current_value and bold_text in current_value:
            new_value = re.sub(
                re.escape(bold_text), f"<b>{bold_text}</b>", current_value, count=1
            )
            self.text_field.value = new_value
            e.control.value = ""  # Clear the bolding field
            self.page.update()
