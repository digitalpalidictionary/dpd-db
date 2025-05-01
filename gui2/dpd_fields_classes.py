import flet as ft


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
            # max_lines=6,
            min_lines=1,
        )


class DpdText(ft.Text):
    def __init__(
        self,
    ):
        super().__init__(
            expand=True,
            selectable=True,
            color=ft.Colors.GREY_500,
            size=16,
            width=700,
        )


class DpdDropdown(ft.Dropdown):
    def __init__(
        self,
        options=None,
        on_focus=None,
        on_change=None,
        on_blur=None,
    ):
        if not options:
            raise ValueError("Options must be provided for DpdDropdown")
        super().__init__(
            expand=True,
            options=[ft.dropdown.Option(o) for o in options],
            on_focus=on_focus,
            on_change=on_change,
            on_blur=on_blur,
            editable=True,
            enable_filter=True,
            width=700,
        )
