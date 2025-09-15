import flet as ft


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
    page.open(snackbar)
    page.update()
