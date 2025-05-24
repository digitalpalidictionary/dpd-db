import flet as ft

from gui2.dpd_fields_classes import DpdTextField
from tools.spelling import CustomSpellChecker


class DpdMeaningField(ft.Column):
    def __init__(
        self,
        ui,
        field_name,
        dpd_fields,
        spellchecker: CustomSpellChecker,
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
        self.spellchecker = spellchecker  # Store spellchecker instance

        # Main meaning field - use the passed handlers for this one
        self.meaning_field = DpdTextField(
            name=field_name,
            multiline=True,
            on_focus=self._handle_spell_check,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=self._handle_spell_check,
        )

        # Field to add words to the dictionary
        self.add_to_dict_field = ft.TextField(
            label="Add spelling ",
            label_style=ft.TextStyle(color=ft.Colors.GREY_700, size=10),
            dense=True,
            text_size=12,
            on_submit=self._handle_add_to_dict_submit,
            color=ft.Colors.RED,
        )

        self.controls = [
            self.meaning_field,
            ft.Row(
                [self.add_to_dict_field],
                spacing=5,
            ),
        ]

    @property
    def value(self):
        return self.meaning_field.value

    @property
    def field(self):
        return self.meaning_field

    @value.setter
    def value(self, value):
        self.meaning_field.value = value

    @property
    def error_text(self):
        """Gets the error text from the internal meaning field."""
        return self.meaning_field.error_text

    @error_text.setter
    def error_text(self, value):
        """Sets the error text on the internal meaning field and updates it."""
        self.meaning_field.error_text = value
        self.meaning_field.update()

    def _handle_add_to_dict_submit(self, e: ft.ControlEvent):
        word_to_add = e.control.value
        if word_to_add:
            message = self.spellchecker.add_to_dictionary(word_to_add)
            self.ui.update_message(message)
            e.control.value = ""
            self.page.update()
            self.meaning_field.focus()

    def _handle_spell_check(self, e: ft.ControlEvent):
        """Common logic for spell checking the meaning field."""
        field = e.control
        value = field.value
        misspelled = self.spellchecker.check_sentence(value)
        if misspelled:
            error_string = ". ".join(
                [
                    f"{word}: {', '.join(suggestions)}"
                    for word, suggestions in misspelled.items()  # type: ignore
                ]
            )
            field.error_text = error_string
        else:
            field.error_text = None
        self.page.update()
