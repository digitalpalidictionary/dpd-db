from typing import Callable

import flet as ft

from gui2.ui_utils import field_border, request_focus


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

    # Flet 1.0 renamed TextField.error_text to `error` but left
    # Dropdown.error_text alone, so the two control types now spell it
    # differently. Assigning the old name on a 1.0 TextField is silently
    # accepted — it writes a dead instance attribute that never reaches the UI —
    # which killed every validation message in the editor at once. Forwarding
    # here keeps the ~60 call sites, and the composite wrappers that delegate to
    # them, spelling it the one way that works on both.
    @property
    def error_text(self) -> str | None:
        value = self.error
        return value if isinstance(value, str) or value is None else None

    @error_text.setter
    def error_text(self, value: str | None) -> None:
        self.error = value

    # 0.28 recoloured the border by itself whenever an error was set. 1.0
    # resolves the error state against the theme, which an explicit `border=`
    # overrides — and every field now carries one (BR-22). Deriving it here
    # rather than at the ~60 assignment sites means no call site has to
    # remember, and clearing the error clears the red with it.
    def before_update(self) -> None:
        super().before_update()
        self.border = (
            field_border(color=ft.Colors.RED) if self.error else field_border()
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

        # Set before super().__init__ so _handle_select can never observe it
        # missing, whatever the base class does during construction.
        self._on_change: Callable[[ft.Event[ft.Dropdown]], None] | None = on_change

        super().__init__(
            # Same `expand` + `width` pair as DpdTextField, deliberately. 1.0
            # resolves the contradiction in favour of `expand`, so both control
            # types settle at the same rendered width and their right edges line
            # up down the form. A fixed `width` here with no `expand` made the
            # dropdowns ~65px wider than the text fields beside them.
            expand=True,
            options=[ft.dropdown.Option(o) for o in options],
            on_focus=on_focus,
            # Flet 1.0 split 0.28's on_change into on_select (an item was
            # picked) and on_text_change (the user typed). on_select is the
            # one that preserves 0.28 behaviour. The parameter keeps its name
            # because it is shared with FieldConfig.on_change across all 48
            # field definitions.
            on_select=self._handle_select,
            on_blur=on_blur,
            editable=True,
            enable_filter=True,
            width=700,
            menu_width=200,
            border=field_border(color=ft.Colors.GREY_800),
        )
        self.name = name

    # 1.0's editable Dropdown is a Flutter dropdown-menu: the options live in an
    # overlay route, so the control holding focus when an option is chosen is
    # destroyed with the overlay and focus falls back to the page root. The next
    # Tab then restarts traversal at the top tab bar instead of moving to the
    # next field. Reclaiming focus here restores 0.28's behaviour.
    #
    # The reclaim runs before the configured handler so that a handler moving
    # focus onward still wins — derivative_change jumping to suffix is the one
    # that does. Focus requests are dispatched in call order, so the later one
    # settles last. Handlers relocating focus from on_blur instead (trans,
    # compound_type) are a separate event and unaffected by this ordering.
    #
    # The handler is called directly rather than through flet's dispatcher, so
    # it must be synchronous and take the event as its single argument.
    def _handle_select(self, e: ft.Event[ft.Dropdown]) -> None:
        request_focus(self)
        if self._on_change is not None:
            self._on_change(e)

    # Dropdown kept 0.28's `error_text` spelling where TextField renamed it to
    # `error`, so no forwarding property is needed here — only the border, for
    # the same reason as DpdTextField.before_update.
    def before_update(self) -> None:
        super().before_update()
        self.border = field_border(
            color=ft.Colors.RED if self.error_text else ft.Colors.GREY_800
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
            border=ft.NoInputBorder(),
            dense=True,
            multiline=True,
        )

    # Same 1.0 rename as DpdTextField. No border toggle: this field is a
    # read-only display and deliberately carries no outline at all.
    @property
    def error_text(self) -> str | None:
        value = self.error
        return value if isinstance(value, str) or value is None else None

    @error_text.setter
    def error_text(self, value: str | None) -> None:
        self.error = value
