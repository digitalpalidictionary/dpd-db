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

        self.on_focus_callback = on_focus
        self.on_blur_callback = on_blur

        # Main meaning field - use the passed handlers for this one
        self.meaning_field = DpdTextField(
            name=field_name,
            multiline=True,
            on_focus=self._handle_on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=self._handle_on_blur,
        )

        # Selectable text for spell check suggestions
        self.spell_suggestions = ft.Text(
            selectable=True,
            color=ft.Colors.RED,
            size=12,
            visible=False,
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

        self._skip_spell_check = False

        self.controls = [
            self.meaning_field,
            self.spell_suggestions,
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

    @property
    def color(self):
        return self.meaning_field.color

    @color.setter
    def color(self, value):
        self.meaning_field.color = value
        self.meaning_field.update()

    @property
    def helper_text(self):
        return self.meaning_field.helper_text

    @helper_text.setter
    def helper_text(self, value):
        self.meaning_field.helper_text = value
        self.meaning_field.update()

    def _handle_add_to_dict_submit(self, e: ft.ControlEvent):
        word_to_add = e.control.value
        if word_to_add:
            message = self.spellchecker.add_to_dictionary(word_to_add)
            e.control.value = ""

            # Remove the added word from existing error text
            # instead of re-running the full spell check
            self._remove_word_from_spell_errors(word_to_add)

            self.ui.update_message(message)
            self._skip_spell_check = True
            self.meaning_field.focus()

    def _remove_word_from_spell_errors(self, word: str):
        """Remove a word from the displayed spell check errors without re-running check."""
        current = self.spell_suggestions.value
        if not current:
            return

        # Error format: "word1: sug1, sug2. word2: sug3, sug4"
        parts = [p.strip() for p in current.split(". ") if p.strip()]
        filtered = [p for p in parts if not p.startswith(f"{word}:")]
        if filtered:
            self.spell_suggestions.value = ". ".join(filtered)
        else:
            self.spell_suggestions.value = None
            self.spell_suggestions.visible = False

    def _handle_on_focus(self, e: ft.ControlEvent):
        """Handle focus on meaning field, including spell check and callback."""
        if self.on_focus_callback:
            self.on_focus_callback(e)
        if self._skip_spell_check:
            self._skip_spell_check = False
            return
        self._handle_spell_check(e)

    def _handle_on_blur(self, e: ft.ControlEvent):
        """Handle blur on meaning field: spell check then external callback."""
        self._handle_spell_check(e)
        if self.on_blur_callback:
            self.on_blur_callback(e)

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
            self.spell_suggestions.value = error_string
            self.spell_suggestions.visible = True
        else:
            self.spell_suggestions.value = None
            self.spell_suggestions.visible = False
        if self.page:
            self.page.update()
