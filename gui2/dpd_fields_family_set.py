import flet as ft
from typing import List

from gui2.dpd_fields_classes import DpdTextField
from tools.pali_sort_key import pali_sort_key

from tools.fuzzy_tools import find_closest_matches


class DpdFamilySetField(ft.Column):
    def __init__(
        self,
        ui,
        field_name,
        dpd_fields,
        options: List[str],
        on_focus=None,
        on_change=None,
        on_submit=None,
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

        self.family_set_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in options if o],
            label="Add Set",
            label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
            dense=True,
            text_size=12,
            on_change=self._handle_dropdown_change,
            enable_filter=True,
            editable=True,
        )

        self.family_set_textfield = DpdTextField(
            name=field_name,
            multiline=False,
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=self._handle_blur,
        )

        self.controls = [
            self.family_set_textfield,
            self.family_set_dropdown,
        ]

    def _handle_dropdown_change(self, e: ft.ControlEvent):
        selected_value = e.control.value
        if not selected_value:
            return

        current_text = self.family_set_textfield.value or ""
        current_sets = set(
            part.strip() for part in current_text.split(";") if part.strip()
        )

        if selected_value not in current_sets:
            current_sets.add(selected_value)
            sorted_sets = sorted(list(current_sets), key=pali_sort_key)
            self.family_set_textfield.value = "; ".join(sorted_sets)

        # Reset dropdown after selection
        e.control.value = ""
        self.page.update()
        self.family_set_textfield.focus()  # Keep focus on the text field

    def _handle_blur(self, e: ft.ControlEvent) -> None:
        """Validate family_set entries against the known list on blur."""
        textfield_control = e.control
        value = textfield_control.value

        if value:
            parts = [part.strip() for part in value.split(";") if part.strip()]
            unknown_parts = []
            known_sets = self.dpd_fields.db.all_family_sets or []

            suggestions_dict = {}
            for part in parts:
                if part not in known_sets:
                    unknown_parts.append(part)
                    suggestions = find_closest_matches(part, known_sets, limit=3)
                    if suggestions:
                        suggestions_dict[part] = suggestions

            if unknown_parts:
                suggestion_strings = []
                for p in unknown_parts:
                    suggestion_strings.extend(suggestions_dict.get(p, []))
                textfield_control.error_text = (
                    ", ".join(suggestion_strings)
                    if suggestion_strings
                    else "Unknown set(s)"
                )
                textfield_control.focus()
            else:
                textfield_control.error_text = None
        else:
            textfield_control.error_text = None
        self.page.update()

    @property
    def value(self):
        return self.family_set_textfield.value

    @property
    def field(self):
        return self.family_set_textfield

    @value.setter
    def value(self, value):
        self.family_set_textfield.value = value

    @property
    def error_text(self):
        return self.family_set_textfield.error_text

    @error_text.setter
    def error_text(self, value):
        self.family_set_textfield.error_text = value
        self.family_set_textfield.update()
