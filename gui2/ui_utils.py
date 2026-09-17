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

    Leaving `color` unset keeps the Material theme's per-state colours, which
    is what the deprecated `border_radius`-only fields used to get.
    """
    side = None if color is None else ft.BorderSide(width=width, color=color)
    return ft.OutlineInputBorder(border_radius=radius, side=side)


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
