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
            border_radius=20,
        )


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
            expand=True,
            options=[ft.dropdown.Option(o) for o in options],
            on_focus=on_focus,
            on_change=on_change,
            on_blur=on_blur,
            editable=True,
            enable_filter=True,
            width=700,
            menu_width=200,
            border_color=ft.Colors.GREY_800,
            border_radius=20,
            border_width=1,
        )


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
            border=ft.InputBorder.NONE,
            dense=True,
            multiline=True,
        )
