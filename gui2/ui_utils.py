import flet as ft


def page_of(control: ft.BaseControl) -> ft.Page | None:
    """The control's page, or None when it is not mounted.

    Flet 1.0 turned `Control.page` into a property that walks up to the `Page`
    and **raises `RuntimeError` when it finds none**. In 0.28 it was a plain
    attribute that read `None`, so the whole codebase tests for mounting with
    `if control.page`/`if control.page is None` — an idiom that now raises the
    very error it was written to avoid.
    """
    try:
        return control.page
    except RuntimeError:
        return None


def is_mounted(control: ft.BaseControl) -> bool:
    """Whether the control is attached to a page. See `page_of`."""
    return page_of(control) is not None


def request_focus(control: ft.BaseControl) -> None:
    """Move focus to `control` from synchronous handler code.

    Flet 1.0 made `Control.focus()` a coroutine. Calling it without awaiting is
    silent — no error, no focus — which made every "move to the next field"
    in the editor a no-op, so focus fell back to whichever control carries
    `autofocus` and the cursor jumped to the top of the form after each edit.

    `focus()` only sends a fire-and-forget message to the client
    (`await self._invoke_method("focus")`), so scheduling it on the page's loop
    is faithful to 0.28 and keeps the ~50 calling handlers synchronous.
    """
    page = page_of(control)
    if page is not None:
        page.run_task(control.focus)  # pyright: ignore[reportAttributeAccessIssue]


FIELD_RADIUS = 20
"""The editor's standard corner radius for text fields and dropdowns."""

FIELD_BORDER_COLOUR = ft.Colors.GREY_800
"""The editor's standard resting border colour for a form field.

Measured, not chosen: 0.28 rendered an unstyled field's outline at exactly
`#424242`, which is this constant. 1.0's dark theme resolves the same unstyled
field to `#8d9199` — over twice as bright — which is why every text field
looked white next to the dropdowns, those having always named the colour
themselves.
"""


def field_border(
    color: ft.ColorValue | None = None,
    width: float = 1.0,
    radius: float = FIELD_RADIUS,
) -> ft.OutlineInputBorder:
    """The standard rounded border for a `TextField` or `Dropdown`.

    Flet 1.0 deprecated `border_radius` / `border_color` / `border_width` on
    form fields in favour of a single `border=` object, and changed the
    Dart-side default from a rounded outline to a square one — so fields that
    set nothing at all lost their corners. Every field now states its border
    explicitly through this helper rather than relying on the default.

    `color` defaults to the resting colour rather than to the theme, so that
    every field matches. Only the focused and error states stay
    theme-resolved — stating a side styles the enabled state alone, which is
    the same division 0.28 had.
    """
    resolved = FIELD_BORDER_COLOUR if color is None else color
    return ft.OutlineInputBorder(
        border_radius=radius, side=ft.BorderSide(width=width, color=resolved)
    )


def set_error(field: ft.TextField, message: str | None) -> None:
    """Set a bare `TextField`'s error message and colour its border to match.

    The `Dpd*` field classes derive this in `before_update()`, but a bare
    `ft.TextField` has no such hook. 1.0 resolves the error state against the
    theme, which the explicit `border=` these fields carry overrides — so
    without this the message appears and the outline stays grey, where 0.28
    turned it red.

    Only for fields whose resting border is the default `field_border()`. A
    field with its own resting colour would come back from an error wearing
    the wrong one.
    """
    field.error = message
    field.border = field_border(color=ft.Colors.RED) if message else field_border()


def show_global_snackbar(
    page: ft.Page,
    message: str,
    snack_type: str = "info",
    duration: int = 4000,
) -> None:
    """Display a standardized SnackBar with type-based styling."""
    if snack_type == "info":
        bgcolor = ft.Colors.BLUE_900
        text_color = ft.Colors.WHITE
    elif snack_type == "warning":
        bgcolor = ft.Colors.ORANGE
        text_color = ft.Colors.BLACK
    elif snack_type == "error":
        bgcolor = ft.Colors.RED
        text_color = ft.Colors.BLACK
    else:
        # Default to info
        bgcolor = ft.Colors.BLUE_900
        text_color = ft.Colors.WHITE

    snackbar = ft.SnackBar(
        content=ft.Text(message, color=text_color),
        bgcolor=bgcolor,
        duration=duration,
    )
    page.show_dialog(snackbar)
