import flet as ft
import re

from gui2.dpd_fields_classes import DpdTextField


class DpdNotesField(ft.Column):
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

        self.notes_field = DpdTextField(
            name=field_name,
            multiline=True,  # Notes are often multiline
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
        )

        self.italicizing_field = ft.TextField(
            label="Italic",
            label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
            dense=True,
            text_size=12,
            on_submit=self._handle_italicizing_submit,
        )

        self.bolding_field = ft.TextField(
            label="Bold",
            label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
            dense=True,
            text_size=12,
            on_submit=self._handle_bolding_submit,
        )

        self.controls = [
            self.notes_field,
            ft.Row(
                [self.italicizing_field, self.bolding_field],
                spacing=5,  # Add some space between the fields
            ),
        ]

    @property
    def value(self):
        return self.notes_field.value

    @property
    def field(self):
        return self.notes_field

    @value.setter
    def value(self, value):
        self.notes_field.value = value

    @property
    def error_text(self):
        """Gets the error text from the internal notes field."""
        return self.notes_field.error_text

    @error_text.setter
    def error_text(self, value):
        """Sets the error text on the internal notes field and updates it."""
        self.notes_field.error_text = value
        self.notes_field.update()

    def _handle_italicizing_submit(self, e: ft.ControlEvent):
        italic_text = e.control.value
        current_value = self.notes_field.value
        if italic_text and current_value and italic_text in current_value:
            # Use non-greedy match for replacement if needed, but simple replace often works
            new_value = re.sub(
                re.escape(italic_text), f"<i>{italic_text}</i>", current_value, count=1
            )
            self.notes_field.value = new_value
            e.control.value = ""
            self.page.update()
            self.notes_field.focus()

    def _handle_bolding_submit(self, e: ft.ControlEvent):
        bold_text = e.control.value
        current_value = self.notes_field.value
        if bold_text and current_value and bold_text in current_value:
            # Use non-greedy match for replacement if needed, but simple replace often works
            new_value = re.sub(
                re.escape(bold_text), f"<b>{bold_text}</b>", current_value, count=1
            )
            self.notes_field.value = new_value
            e.control.value = ""
            self.page.update()
            self.notes_field.focus()
