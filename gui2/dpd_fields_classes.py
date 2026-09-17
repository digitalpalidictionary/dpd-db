import flet as ft
from gui2.ui_utils import field_border


class FieldConfig:
    def __init__(
        self,
        name,
        field_type="text",
        options=None,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
        multiline=False,
    ):
        self.name = name
        self.field_type = field_type
        self.options = options
        self.on_focus = on_focus
        self.on_change = on_change
        self.on_submit = on_submit
        self.on_blur = on_blur
        self.multiline = multiline


class DpdTextField(ft.TextField):
    def __init__(
        self,
        name,
        on_focus=None,
        on_change=None,
        on_submit=None,
        on_blur=None,
        multiline=False,
    ):
        super().__init__(
            expand=True,
            multiline=multiline,
            on_focus=on_focus,
            on_change=on_change,
            on_submit=on_submit,
            on_blur=on_blur,
            min_lines=1,
            width=700,
            border=field_border(),
        )
        self.name = name


class DpdDropdown(ft.Dropdown):
    def __init__(
        self,
        name,
        options=None,
        on_focus=None,
        on_change=None,
        on_blur=None,
    ):
        if options is None:  # Check specifically for None, allow empty list
            raise ValueError("Options must be provided for DpdDropdown")

        super().__init__(
            # No `expand`: it and `width` contradict each other, and 1.0 resolves
            # that the opposite way to 0.28 — the dropdowns stretched to the full
            # row instead of stopping at 700. The text fields are left expanding
            # because that is what they did in 0.28.
            options=[ft.dropdown.Option(o) for o in options],
            on_focus=on_focus,
            # Flet 1.0 split 0.28's on_change into on_select (an item was
            # picked) and on_text_change (the user typed). on_select is the
            # one that preserves 0.28 behaviour. The parameter keeps its name
            # because it is shared with FieldConfig.on_change across all 48
            # field definitions.
            on_select=on_change,
            on_blur=on_blur,
            editable=True,
            enable_filter=True,
            width=700,
            menu_width=200,
            border=field_border(color=ft.Colors.GREY_800),
        )
        self.name = name


class DpdText(ft.TextField):
    def __init__(
        self,
    ):
        super().__init__(
            expand=False,
            color=ft.Colors.GREY_500,
            text_size=16,
            width=500,
            read_only=True,
            border=ft.NoInputBorder(),
            dense=True,
            multiline=True,
        )
