# -*- coding: utf-8 -*-
import flet as ft

from db.models import DpdRoot
from gui2.toolkit import ToolKit
from gui2.ui_utils import show_global_snackbar

GROUP_LABEL_WIDTH = 150
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
BUTTON_WIDTH = 200


class RootsTabView(ft.Column):
    """Full CRUD editor for the dpd_roots table."""

    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])

        self.page = page
        self.toolkit = toolkit
        self._db = toolkit.db_manager

        self._current_root_key: str | None = None
        self._is_new_mode: bool = False

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        top = self._build_top_section()
        middle = self._build_middle_section()
        bottom = self._build_bottom_section()
        self.controls = [top, middle, bottom]

    def _build_top_section(self) -> ft.Container:
        self._root_dropdown = ft.Dropdown(
            hint_text="Select root",
            hint_style=ft.TextStyle(color=LABEL_COLOUR),
            options=self._get_dropdown_options(),
            editable=True,
            enable_filter=True,
            expand=True,
            border_radius=20,
            border_color=ft.Colors.GREY_800,
            border_width=1,
            text_size=14,
            on_change=self._on_dropdown_change,
        )

        self._message_field = ft.TextField(
            "",
            read_only=True,
            expand=True,
            border_color=HIGHLIGHT_COLOUR,
            border_radius=20,
            color=HIGHLIGHT_COLOUR,
            hint_text="Messages",
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            text_size=14,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._root_dropdown,
                            ft.ElevatedButton(
                                "New", on_click=self._new_root, width=BUTTON_WIDTH
                            ),
                            ft.ElevatedButton(
                                "Clear", on_click=self._clear_all, width=BUTTON_WIDTH
                            ),
                            self._message_field,
                        ],
                        spacing=10,
                    ),
                ]
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
        )

    def _build_middle_section(self) -> ft.Container:
        # Each tuple: (group_label, [(field_name, expand_int), ...], multiline_field)
        # Every group renders as ONE row: [group label] [field1] [field2] ...
        rows: list[ft.Row] = [
            self._make_group_row(
                "Root Info",
                [
                    ("root", 1),
                    ("root_in_comps", 1),
                    ("root_has_verb", 1),
                    ("root_group", 1),
                    ("root_sign", 1),
                    ("root_meaning", 2),
                    ("root_example", 2),
                ],
            ),
            self._make_group_row(
                "Sanskrit",
                [
                    ("sanskrit_root", 1),
                    ("sanskrit_root_meaning", 2),
                    ("sanskrit_root_class", 1),
                ],
            ),
            self._make_group_row(
                "Dhātupāṭha",
                [
                    ("dhatupatha_num", 1),
                    ("dhatupatha_root", 1),
                    ("dhatupatha_pali", 2),
                    ("dhatupatha_english", 2),
                ],
            ),
            self._make_group_row(
                "Dhātumañjūsa",
                [
                    ("dhatumanjusa_num", 1),
                    ("dhatumanjusa_root", 1),
                    ("dhatumanjusa_pali", 2),
                    ("dhatumanjusa_english", 2),
                ],
            ),
            self._make_group_row(
                "Saddanīti",
                [
                    ("dhatumala_root", 1),
                    ("dhatumala_pali", 2),
                    ("dhatumala_english", 2),
                ],
            ),
            self._make_group_row(
                "Pāṇini",
                [
                    ("panini_root", 1),
                    ("panini_sanskrit", 1),
                    ("panini_english", 2),
                ],
            ),
            self._make_group_row(
                "Other",
                [
                    ("note", 3, True),
                    ("matrix_test", 1),
                ],
            ),
        ]  # type: ignore

        return ft.Container(
            content=ft.Column(
                controls=rows,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                spacing=4,
            ),
            expand=True,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )

    def _build_bottom_section(self) -> ft.Container:
        self._delete_button = ft.ElevatedButton(
            "Delete",
            on_click=self._delete_root,
            width=BUTTON_WIDTH,
            on_hover=self._on_delete_hover,
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.ElevatedButton(
                        "Save to DB",
                        on_click=self._save_root,
                        width=BUTTON_WIDTH,
                    ),
                    self._delete_button,
                ],
                spacing=10,
            ),
            padding=ft.padding.all(10),
        )

    # ── Helper builders ───────────────────────────────────────────────────────

    def _make_field(
        self, name: str, expand: int = 1, multiline: bool = False
    ) -> ft.TextField:
        field = ft.TextField(
            expand=expand,
            border_radius=10,
            multiline=multiline,
            min_lines=1,
            max_lines=4 if multiline else 1,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )
        setattr(self, f"_field_{name}", field)
        return field

    def _make_group_row(self, group_name: str, fields: list[tuple]) -> ft.Column:
        """Two-row block per group: labels above, fields below, perfectly aligned.

        Each entry in fields is (name, expand) or (name, expand, multiline).
        """
        label_controls: list[ft.Control] = [ft.Container(width=GROUP_LABEL_WIDTH)]
        field_controls: list[ft.Control] = [
            ft.Text(
                group_name,
                width=GROUP_LABEL_WIDTH,
                color=LABEL_COLOUR,
                size=12,
                selectable=True,
                no_wrap=True,
            )
        ]

        for entry in fields:
            name = entry[0]
            expand = entry[1] if len(entry) > 1 else 1
            multiline = entry[2] if len(entry) > 2 else False
            label_controls.append(
                ft.Text(name, expand=expand, color=LABEL_COLOUR, size=11, no_wrap=True)
            )
            field_controls.append(
                self._make_field(name, expand=expand, multiline=multiline)
            )

        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(controls=label_controls, spacing=6),
                    padding=ft.padding.only(top=6, bottom=2),
                ),
                ft.Row(
                    controls=field_controls,
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=0,
        )

    # ── Dropdown helpers ──────────────────────────────────────────────────────

    def _get_dropdown_options(self) -> list[ft.dropdown.Option]:
        keys = self._db.get_all_root_keys_sorted()
        return [ft.dropdown.Option(k) for k in keys]

    def _refresh_dropdown(self) -> None:
        self._root_dropdown.options = self._get_dropdown_options()
        self._root_dropdown.update()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_dropdown_change(self, e: ft.ControlEvent) -> None:
        selected = self._root_dropdown.value
        if selected:
            self._load_root(selected)

    def _on_delete_hover(self, e: ft.ControlEvent) -> None:
        e.control.bgcolor = ft.Colors.RED if e.data == "true" else None
        e.control.color = "white" if e.data == "true" else None
        e.control.update()

    # ── CRUD logic ────────────────────────────────────────────────────────────

    def _load_root(self, root_key: str) -> None:
        self._db.new_db_session()
        root = self._db.get_root_by_key(root_key)
        if root is None:
            self._set_message(f"Root '{root_key}' not found")
            return

        self._current_root_key = root_key
        self._is_new_mode = False

        for col in DpdRoot.__table__.columns:
            if col.name in ("created_at", "updated_at", "root_info", "root_matrix"):
                continue
            field: ft.TextField | None = getattr(self, f"_field_{col.name}", None)
            if field is not None:
                val = getattr(root, col.name)
                field.value = str(val) if val is not None else ""

        self._set_message(f"Loaded: {root_key}")
        self.page.update()  # type: ignore

    def _save_root(self, e: ft.ControlEvent) -> None:
        root_field: ft.TextField = getattr(self, "_field_root")
        root_key = (root_field.value or "").strip()

        if not root_key:
            show_global_snackbar(self.page, "Root field is empty", "error")  # type: ignore
            return

        # Auto-prefix √ for new roots
        if self._is_new_mode and not root_key.startswith("√"):
            root_key = f"√{root_key}"
            root_field.value = root_key
            root_field.update()

        new_root = self._build_root_from_fields(root_key)

        if self._is_new_mode:
            success, msg = self._db.add_root_to_db(new_root)
            action = "Added"
        else:
            original_key = self._current_root_key or root_key
            success, msg = self._db.update_root_in_db(original_key, new_root)
            action = "Saved"

        if success:
            self._current_root_key = root_key
            self._is_new_mode = False
            self._refresh_dropdown()
            self._root_dropdown.value = root_key
            self._root_dropdown.update()
            show_global_snackbar(self.page, f"{action}: {root_key}", "info")  # type: ignore
        else:
            show_global_snackbar(self.page, f"Error: {msg}", "error", 6000)  # type: ignore

    def _new_root(self, e: ft.ControlEvent) -> None:
        self._clear_fields()
        self._is_new_mode = True
        self._current_root_key = None
        self._root_dropdown.value = None
        self._root_dropdown.update()
        root_field: ft.TextField = getattr(self, "_field_root")
        root_field.value = "√"
        self._set_message("New root — enter fields and save")
        self.page.update()  # type: ignore
        root_field.focus()

    def _delete_root(self, e: ft.ControlEvent) -> None:
        if self._is_new_mode or self._current_root_key is None:
            show_global_snackbar(self.page, "No root loaded to delete", "warning")  # type: ignore
            return

        root_key = self._current_root_key
        count = self._db.get_root_headword_count(root_key)

        def confirm_delete(dialog_e: ft.ControlEvent) -> None:
            self.page.close(dlg)  # type: ignore
            success, msg = self._db.delete_root_in_db(root_key)
            if success:
                self._current_root_key = None
                self._is_new_mode = False
                self._clear_fields()
                self._refresh_dropdown()
                show_global_snackbar(self.page, f"Deleted: {root_key}", "info")  # type: ignore
            else:
                show_global_snackbar(self.page, f"Error: {msg}", "error", 6000)  # type: ignore

        def cancel_delete(dialog_e: ft.ControlEvent) -> None:
            self.page.close(dlg)  # type: ignore

        warning = (
            f"Delete '{root_key}'?\n\n⚠ {count} headword(s) reference this root."
            if count > 0
            else f"Delete '{root_key}'?"
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(warning),
            actions=[
                ft.TextButton("Delete", on_click=confirm_delete),
                ft.TextButton("Cancel", on_click=cancel_delete),
            ],
        )
        self.page.open(dlg)  # type: ignore

    def _clear_all(self, e: ft.ControlEvent | None = None) -> None:
        self._clear_fields()
        self._current_root_key = None
        self._is_new_mode = False
        self._root_dropdown.value = None
        self._root_dropdown.update()
        self._set_message("")
        self.page.update()  # type: ignore

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _clear_fields(self) -> None:
        for col in DpdRoot.__table__.columns:
            if col.name in ("created_at", "updated_at", "root_info", "root_matrix"):
                continue
            field: ft.TextField | None = getattr(self, f"_field_{col.name}", None)
            if field is not None:
                field.value = ""

    def _build_root_from_fields(self, root_key: str) -> DpdRoot:
        root = DpdRoot()
        for col in DpdRoot.__table__.columns:
            if col.name in ("created_at", "updated_at", "root_info", "root_matrix"):
                continue
            field: ft.TextField | None = getattr(self, f"_field_{col.name}", None)
            if field is None:
                continue
            raw = (field.value or "").strip()
            # root_group and dhatumanjusa_num are int columns
            if col.type.python_type is int:
                try:
                    setattr(root, col.name, int(raw) if raw else 0)
                except ValueError:
                    setattr(root, col.name, 0)
            else:
                setattr(root, col.name, raw)
        root.root = root_key
        return root

    def _set_message(self, msg: str) -> None:
        self._message_field.value = msg
        if hasattr(self, "page") and self.page:
            self._message_field.update()
