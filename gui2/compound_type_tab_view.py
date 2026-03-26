import re
from pathlib import Path

import flet as ft

from db.models import DpdHeadword
from gui2.filter_component import CellTextField, DpdDatatable
from gui2.toolkit import ToolKit
from gui2.ui_utils import show_global_snackbar
from tools.compound_type_manager import CompoundTypeManager
from tools.pali_sort_key import pali_list_sorter

LABEL_COLOUR = ft.Colors.GREY_500
TSV_PATH = Path("tools/compound_type_manager.tsv")
MAX_RESULTS = 200

DISPLAY_COLUMNS = [
    "lemma_1",
    "pos",
    "meaning_1",
    "compound_type",
    "compound_construction",
]
COLUMN_WIDTHS = [200, 80, 350, 150, 300]


class CompoundTypeTabView(ft.Column):
    """CT tab — manage compound type rules and search dpd_headwords."""

    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page = page
        self.toolkit = toolkit
        self._ct_manager = CompoundTypeManager(TSV_PATH)
        self._current_rule_key: tuple[str, str, str] | None = None
        self._current_rule_index: int = 0
        self._current_word_matches: list[dict] = []
        self._search_results: list[DpdHeadword] = []
        self._modified_cells: dict[tuple[int, str], str] = {}
        self._selected_types: list[str] = []
        # Row index to focus after table rebuild (e.g. after exception add).
        # -1 means no focus requested.
        self._focus_after_rebuild: int = -1
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.controls = [
            self._build_fields_section(),
            self._build_buttons_section(),
            self._build_results_section(),
            self._build_save_section(),
        ]

    def _build_fields_section(self) -> ft.Container:
        self._word_field = ft.TextField(
            hint_text="word",
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            border_radius=20,
            border_color=ft.Colors.GREY_800,
            border_width=1,
            text_size=14,
            expand=2,
            helper_text=" ",
            helper_style=ft.TextStyle(color=ft.Colors.BLUE_200, size=10),
            on_submit=self._on_word_submit,
        )
        helper_style = ft.TextStyle(color=ft.Colors.BLUE_200, size=10)
        self._pos_dropdown = ft.Dropdown(
            hint_text="pos",
            hint_style=ft.TextStyle(color=LABEL_COLOUR),
            options=self._get_options("pos", include_any=True),
            expand=1,
            border_radius=20,
            border_color=ft.Colors.GREY_800,
            border_width=1,
            text_size=14,
            helper_text=" ",
            helper_style=helper_style,
            on_change=lambda e: setattr(
                e.control, "helper_text", e.control.value or " "
            )
            or e.control.update(),
        )
        self._position_dropdown = ft.Dropdown(
            hint_text="position",
            hint_style=ft.TextStyle(color=LABEL_COLOUR),
            options=[
                ft.dropdown.Option("first"),
                ft.dropdown.Option("middle"),
                ft.dropdown.Option("last"),
                ft.dropdown.Option("any"),
            ],
            editable=True,
            enable_filter=True,
            expand=1,
            border_radius=20,
            border_color=ft.Colors.GREY_800,
            border_width=1,
            text_size=14,
            helper_text=" ",
            helper_style=helper_style,
            on_change=lambda e: setattr(
                e.control, "helper_text", e.control.value or " "
            )
            or e.control.update(),
        )
        self._type_dropdown = ft.Dropdown(
            hint_text="type",
            hint_style=ft.TextStyle(color=LABEL_COLOUR),
            options=self._get_options("type"),
            editable=True,
            enable_filter=True,
            expand=2,
            border_radius=20,
            border_color=ft.Colors.GREY_800,
            border_width=1,
            text_size=14,
            menu_width=350,
            helper_text=" ",
            helper_style=helper_style,
        )
        self._type_add_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            on_click=self._on_type_add,
            tooltip="Add type",
        )
        self._type_chips_row = ft.Row(wrap=True, spacing=4, run_spacing=4)
        self._exceptions_field = ft.TextField(
            hint_text="exceptions (comma-separated)",
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            border_radius=20,
            border_color=ft.Colors.GREY_800,
            border_width=1,
            text_size=14,
            multiline=True,
            min_lines=1,
            max_lines=6,
            expand=True,
        )
        self._notes_field = ft.TextField(
            hint_text="notes",
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            border_radius=20,
            border_color=ft.Colors.GREY_800,
            border_width=1,
            text_size=14,
            multiline=True,
            min_lines=1,
            max_lines=6,
            expand=True,
        )
        type_input = ft.Row(
            [self._type_dropdown, self._type_add_button],
            spacing=4,
            expand=2,
        )
        row1 = ft.Row(
            [
                self._word_field,
                self._pos_dropdown,
                self._position_dropdown,
                type_input,
            ],
            spacing=8,
        )
        row1b = ft.Row([self._type_chips_row], spacing=8)
        row2 = ft.Row([self._exceptions_field], spacing=8)
        row3 = ft.Row([self._notes_field], spacing=8)
        return ft.Container(
            content=ft.Column([row1, row1b, row2, row3], spacing=6),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_800)),
        )

    def _build_buttons_section(self) -> ft.Container:
        self._message_field = ft.TextField(
            read_only=True,
            expand=True,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            color=ft.Colors.BLUE_200,
            hint_text="Messages",
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            text_size=13,
        )
        self._add_button = ft.ElevatedButton("Add", on_click=self._on_add)
        self._update_button = ft.ElevatedButton(
            "Update", on_click=self._on_update, visible=False
        )
        self._next_button = ft.ElevatedButton(
            "→", on_click=self._on_next_rule, visible=False
        )
        buttons_row = ft.Row(
            [
                self._next_button,
                self._add_button,
                self._update_button,
                ft.ElevatedButton("All", on_click=self._on_all),
                ft.ElevatedButton("Correct", on_click=self._on_correct),
                ft.ElevatedButton("Wrong", on_click=self._on_wrong),
                ft.ElevatedButton("Exceptions", on_click=self._on_show_exceptions),
                ft.ElevatedButton("Clear", on_click=self._on_clear),
                ft.ElevatedButton(
                    "Delete",
                    on_click=self._on_delete,
                    on_hover=self._on_delete_hover,
                ),
                ft.ElevatedButton("TSV", on_click=self._on_open_tsv),
            ],
            spacing=8,
        )
        message_row = ft.Row([self._message_field], spacing=8)
        return ft.Container(
            content=ft.Column([buttons_row, message_row], spacing=4),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )

    def _build_results_section(self) -> ft.Container:
        placeholder_col = ft.DataColumn(label=ft.Text("#"))
        self._results_table = DpdDatatable(columns=[placeholder_col], rows=[])

        table_wrap = ft.Container(content=self._results_table, expand=True)
        hscroll = ft.Row(
            [table_wrap],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            alignment=ft.MainAxisAlignment.START,
        )
        return ft.Container(
            content=ft.Column([hscroll], scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
        )

    def _build_save_section(self) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [ft.ElevatedButton("Save Changes", on_click=self._on_save_changes)],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_options(
        self, field: str, include_any: bool = False
    ) -> list[ft.dropdown.Option]:
        values = self._ct_manager.get_unique_values(field)
        if include_any:
            prefix = [v for v in ["any", "noun"] if v not in values]
            values = prefix + values
        return [ft.dropdown.Option(v) for v in values]

    def _on_type_add(self, e: ft.ControlEvent) -> None:
        type_val = (self._type_dropdown.value or "").strip()
        if not type_val or type_val in self._selected_types:
            return
        self._selected_types.append(type_val)
        self._type_dropdown.value = None
        self._rebuild_type_chips()
        self._type_dropdown.update()

    def _on_type_chip_delete(self, type_val: str) -> None:
        if type_val in self._selected_types:
            self._selected_types.remove(type_val)
            self._rebuild_type_chips()

    def _rebuild_type_chips(self) -> None:
        self._type_chips_row.controls = [
            ft.Chip(
                label=ft.Text(t, size=12, selectable=True),
                on_delete=lambda e, tv=t: self._on_type_chip_delete(tv),
                bgcolor=ft.Colors.BLUE_GREY_800,
            )
            for t in self._selected_types
        ]
        self._type_chips_row.update()

    def _get_type_string(self) -> str:
        return " | ".join(self._selected_types)

    def _refresh_dropdowns(self) -> None:
        self._pos_dropdown.options = self._get_options("pos", include_any=True)
        self._pos_dropdown.update()
        self._type_dropdown.options = self._get_options("type")
        self._type_dropdown.update()

    def _set_message(self, msg: str) -> None:
        self._message_field.value = msg
        self._message_field.update()

    def _set_add_button_mode(self, editing: bool) -> None:
        self._update_button.visible = editing
        self._update_button.update()

    def _apply_pos_filter(self, query, pos: str):
        if pos and pos not in ("any", ""):
            if pos == "noun":
                query = query.filter(DpdHeadword.pos.in_(["masc", "fem", "nt"]))
            else:
                query = query.filter(DpdHeadword.pos == pos)
        return query

    def _on_open_tsv(self, e: ft.ControlEvent) -> None:
        try:
            self._ct_manager.open_tsv_for_editing()
            self._set_message(f"Opening TSV: {TSV_PATH}")
        except (FileNotFoundError, RuntimeError) as err:
            self._set_message(f"Error: {err}")

    def _build_search_pattern(self, word: str, position: str) -> str:
        escaped = re.escape(word)
        if position == "first":
            return rf"^{escaped} "
        elif position == "middle":
            return rf" {escaped} "
        elif position == "last":
            return rf" {escaped}$"
        return rf"\b{escaped}\b"

    def _clear_fields(self) -> None:
        self._word_field.value = ""
        self._pos_dropdown.value = None
        self._pos_dropdown.helper_text = " "
        self._position_dropdown.value = None
        self._position_dropdown.helper_text = " "
        self._selected_types = []
        self._rebuild_type_chips()
        self._type_dropdown.value = None
        self._exceptions_field.value = ""
        self._notes_field.value = ""
        self._current_rule_key = None
        self._current_word_matches = []
        self._current_rule_index = 0
        self._next_button.visible = False
        self._next_button.update()
        self._set_add_button_mode(editing=False)

    def _clear_results(self) -> None:
        self._results_table.columns = [ft.DataColumn(label=ft.Text("#"))]
        self._results_table.rows = []
        self._results_table.update()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_word_submit(self, e: ft.ControlEvent) -> None:
        self._ct_manager.reload()
        self._refresh_dropdowns()
        word = (self._word_field.value or "").strip()
        if not word:
            self._current_rule_key = None
            self._set_add_button_mode(editing=False)
            return
        matches = self._ct_manager.get_rules_by_word(word)
        if matches:
            self._current_word_matches = matches
            self._current_rule_index = 0
            self._load_rule_at_index(0)
        else:
            self._current_rule_key = None
            self._current_word_matches = []
            self._current_rule_index = 0
            self._next_button.visible = False
            self._next_button.update()
            self._set_add_button_mode(editing=False)
            self._pos_dropdown.value = None
            self._pos_dropdown.helper_text = " "
            self._position_dropdown.value = None
            self._position_dropdown.helper_text = " "
            self._selected_types = []
            self._rebuild_type_chips()
            self._type_dropdown.value = None
            self._exceptions_field.value = ""
            self._notes_field.value = ""
            self._pos_dropdown.update()
            self._position_dropdown.update()
            self._type_dropdown.update()
            self._exceptions_field.update()
            self._notes_field.update()
            self._set_message(f"No rule found for '{word}'")
        self.page.update()
        self._pos_dropdown.focus()

    def _load_rule_at_index(self, idx: int) -> None:
        rule = self._current_word_matches[idx]
        canonical_word = str(rule["word"])
        self._current_rule_key = (
            canonical_word,
            str(rule["pos"]),
            str(rule["position"]),
        )
        self._word_field.value = canonical_word
        self._pos_dropdown.value = str(rule["pos"])
        self._pos_dropdown.helper_text = str(rule["pos"])
        self._position_dropdown.value = str(rule["position"])
        self._position_dropdown.helper_text = str(rule["position"])
        type_str = str(rule["type"])
        self._selected_types = [t.strip() for t in type_str.split("|") if t.strip()]
        self._rebuild_type_chips()
        self._type_dropdown.value = None
        exceptions = rule.get("exceptions", [])
        self._exceptions_field.value = (
            ", ".join(exceptions) if isinstance(exceptions, list) else str(exceptions)
        )
        self._notes_field.value = str(rule.get("notes", ""))
        self._word_field.update()
        self._pos_dropdown.update()
        self._position_dropdown.update()
        self._type_dropdown.update()
        self._exceptions_field.update()
        self._notes_field.update()
        self._set_add_button_mode(editing=True)
        count = len(self._current_word_matches)
        self._next_button.visible = count > 1
        self._next_button.update()
        self._set_message(
            f"Loaded rule: {canonical_word} [{idx + 1}/{count}]"
            if count > 1
            else f"Loaded rule: {canonical_word}"
        )
        self._on_wrong(None)

    def _on_next_rule(self, e: ft.ControlEvent) -> None:
        if not self._current_word_matches:
            return
        self._current_rule_index = (self._current_rule_index + 1) % len(
            self._current_word_matches
        )
        self._load_rule_at_index(self._current_rule_index)

    def _get_fields(self) -> tuple[str, str, str, str, str, str] | None:
        word = (self._word_field.value or "").strip()
        pos = (self._pos_dropdown.value or "").strip()
        position = (self._position_dropdown.value or "").strip()
        type_ = self._get_type_string()
        exceptions = (self._exceptions_field.value or "").strip()
        notes = (self._notes_field.value or "").strip()
        if not word or not pos or not position or not type_:
            show_global_snackbar(
                self.page, "word, pos, position, and type are required", "error"
            )
            return None
        return word, pos, position, type_, exceptions, notes

    def _on_add(self, e: ft.ControlEvent) -> None:
        fields = self._get_fields()
        if fields is None:
            return
        word, pos, position, type_, exceptions, notes = fields
        self._ct_manager.add_rule(word, pos, position, type_, exceptions, notes)
        self._current_rule_key = (word, pos, position)
        self._current_word_matches = self._ct_manager.get_rules_by_word(word)
        self._current_rule_index = len(self._current_word_matches) - 1
        self._next_button.visible = len(self._current_word_matches) > 1
        self._next_button.update()
        self._set_add_button_mode(editing=True)
        self._set_message(f"Added: {word}")
        self._refresh_dropdowns()
        self._on_wrong(None)

    def _on_update(self, e: ft.ControlEvent) -> None:
        if not self._current_rule_key:
            show_global_snackbar(self.page, "No rule loaded to update", "warning")
            return
        fields = self._get_fields()
        if fields is None:
            return
        word, pos, position, type_, exceptions, notes = fields
        old_word, old_pos, old_position = self._current_rule_key
        self._ct_manager.update_rule(
            old_word,
            old_pos,
            old_position,
            word,
            pos,
            position,
            type_,
            exceptions,
            notes,
        )
        self._current_rule_key = (word, pos, position)
        self._current_word_matches = self._ct_manager.get_rules_by_word(word)
        for i, match in enumerate(self._current_word_matches):
            if str(match["pos"]) == pos and str(match["position"]) == position:
                self._current_rule_index = i
                break
        self._next_button.visible = len(self._current_word_matches) > 1
        self._next_button.update()
        self._set_message(f"Updated: {word}")
        self._refresh_dropdowns()
        self._on_wrong(None)

    def _on_all(self, e: ft.ControlEvent | None) -> None:
        if self._modified_cells:
            show_global_snackbar(self.page, "Save table changes first", "warning")
            return
        self._ct_manager.reload()
        word = (self._word_field.value or "").strip()
        pos = (self._pos_dropdown.value or "").strip()
        position = (self._position_dropdown.value or "").strip()

        if not word:
            show_global_snackbar(self.page, "Enter a word to search", "warning")
            return
        if not position:
            position = "any"

        pattern = self._build_search_pattern(word, position)

        try:
            self.toolkit.db_manager.new_db_session()
            query = self.toolkit.db_manager.db_session.query(DpdHeadword).filter(
                DpdHeadword.construction.regexp_match(pattern),
                DpdHeadword.grammar.regexp_match(r"\bcomp\b"),
            )
            query = self._apply_pos_filter(query, pos)
            results = query.order_by(DpdHeadword.lemma_1).limit(MAX_RESULTS).all()
        except Exception as ex:
            show_global_snackbar(self.page, f"Search error: {ex}", "error")
            return

        self._update_results_table(results)
        self._set_message(f"{len(results)} result(s) for '{word}'")

    def _on_correct(self, e: ft.ControlEvent | None) -> None:
        if self._modified_cells:
            show_global_snackbar(self.page, "Save table changes first", "warning")
            return
        self._ct_manager.reload()
        word = (self._word_field.value or "").strip()
        pos = (self._pos_dropdown.value or "").strip()
        position = (self._position_dropdown.value or "").strip()
        rule_type = self._get_type_string()

        if not word:
            show_global_snackbar(self.page, "Enter a word to search", "warning")
            return
        if not position:
            position = "any"

        pattern = self._build_search_pattern(word, position)
        try:
            self.toolkit.db_manager.new_db_session()
            query = self.toolkit.db_manager.db_session.query(DpdHeadword).filter(
                DpdHeadword.construction.regexp_match(pattern),
                DpdHeadword.grammar.regexp_match(r"\bcomp\b"),
            )
            query = self._apply_pos_filter(query, pos)
            all_results = query.order_by(DpdHeadword.lemma_1).limit(MAX_RESULTS).all()
        except Exception as ex:
            show_global_snackbar(self.page, f"Search error: {ex}", "error")
            return

        rule_types = {p.strip() for p in rule_type.split("|") if p.strip()}
        results = [
            hw
            for hw in all_results
            if any(rt in (hw.compound_type or "") for rt in rule_types)
        ]

        self._update_results_table(results)
        self._set_message(f"{len(results)} correct match(es) for '{word}'")

    def _on_show_exceptions(self, e: ft.ControlEvent | None) -> None:
        if self._modified_cells:
            show_global_snackbar(self.page, "Save table changes first", "warning")
            return

        exceptions_str = (self._exceptions_field.value or "").strip()
        if not exceptions_str:
            show_global_snackbar(self.page, "No exceptions listed", "info", 3000)
            return

        exceptions_list = [ex.strip() for ex in exceptions_str.split(",") if ex.strip()]
        if not exceptions_list:
            show_global_snackbar(self.page, "No exceptions listed", "info", 3000)
            return

        try:
            self.toolkit.db_manager.new_db_session()
            results = (
                self.toolkit.db_manager.db_session.query(DpdHeadword)
                .filter(DpdHeadword.lemma_1.in_(exceptions_list))
                .order_by(DpdHeadword.lemma_1)
                .all()
            )
        except Exception as ex:
            show_global_snackbar(self.page, f"Search error: {ex}", "error")
            return

        self._update_results_table(results)
        self._set_message(f"{len(results)} exception(s) listed")

    def _on_wrong(self, e: ft.ControlEvent | None) -> None:
        if self._modified_cells:
            show_global_snackbar(self.page, "Save table changes first", "warning")
            return
        self._ct_manager.reload()
        word = (self._word_field.value or "").strip()
        pos = (self._pos_dropdown.value or "").strip()
        position = (self._position_dropdown.value or "").strip()
        rule_type = self._get_type_string()

        if not word:
            show_global_snackbar(self.page, "Enter a word to search", "warning")
            return
        if not position:
            position = "any"

        pattern = self._build_search_pattern(word, position)
        try:
            self.toolkit.db_manager.new_db_session()
            query = self.toolkit.db_manager.db_session.query(DpdHeadword).filter(
                DpdHeadword.construction.regexp_match(pattern),
                DpdHeadword.grammar.regexp_match(r"\bcomp\b"),
            )
            query = self._apply_pos_filter(query, pos)
            all_results = query.order_by(DpdHeadword.lemma_1).limit(MAX_RESULTS).all()
        except Exception as ex:
            show_global_snackbar(self.page, f"Search error: {ex}", "error")
            return

        if self._current_rule_key:
            word_key, pos_key, position_key = self._current_rule_key
            loaded_rules = self._ct_manager.get_rules_by_word(word_key)
            rule_obj = next(
                (
                    r
                    for r in loaded_rules
                    if str(r["pos"]) == pos_key and str(r["position"]) == position_key
                ),
                None,
            )
            if rule_obj:
                exc_raw = rule_obj.get("exceptions", [])
                exceptions_set = (
                    set(exc_raw)
                    if isinstance(exc_raw, list)
                    else {e.strip() for e in str(exc_raw).split(",") if e.strip()}
                )
            else:
                exceptions_set = set()
        else:
            exceptions = (self._exceptions_field.value or "").strip()
            exceptions_set = {e.strip() for e in exceptions.split(",") if e.strip()}
        rule_types = {p.strip() for p in rule_type.split("|") if p.strip()}
        results = [
            hw
            for hw in all_results
            if not any(rt in (hw.compound_type or "") for rt in rule_types)
            and hw.lemma_1 not in exceptions_set
        ]

        self._update_results_table(results)
        self._set_message(f"{len(results)} wrong for '{word}'")

    def _on_clear(self, e: ft.ControlEvent) -> None:
        self._modified_cells.clear()
        self._clear_fields()
        self._clear_results()
        self._set_message("")
        self.page.update()

    def _on_delete(self, e: ft.ControlEvent) -> None:
        if not self._current_rule_key:
            show_global_snackbar(self.page, "No rule loaded to delete", "warning")
            return
        word, pos, position = self._current_rule_key

        def confirm(dlg_e: ft.ControlEvent) -> None:
            self.page.close(dlg)
            self._ct_manager.delete_rule(word, pos, position)
            self._refresh_dropdowns()
            remaining = self._ct_manager.get_rules_by_word(word)
            if remaining:
                self._current_word_matches = remaining
                self._current_rule_index = 0
                self._load_rule_at_index(0)
                self._set_message(
                    f"Deleted: {word} — loaded next rule [{1}/{len(remaining)}]"
                )
            else:
                self._clear_fields()
                self._clear_results()
                self._set_message(f"Deleted: {word}")

        def cancel(dlg_e: ft.ControlEvent) -> None:
            self.page.close(dlg)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Delete rule for {word}-{pos}-{position}?"),
            actions=[
                ft.TextButton("Delete", on_click=confirm),
                ft.TextButton("Cancel", on_click=cancel),
            ],
        )
        self.page.open(dlg)

    def _on_delete_hover(self, e: ft.ControlEvent) -> None:
        e.control.bgcolor = ft.Colors.RED if e.data == "true" else None
        e.control.color = "white" if e.data == "true" else None
        e.control.update()

    def _on_exception_add(self, lemma: str, row_idx: int) -> None:
        if self._modified_cells:
            show_global_snackbar(self.page, "Save table changes first", "warning")
            return
        current = (self._exceptions_field.value or "").strip()
        exceptions_set = {e.strip() for e in current.split(",") if e.strip()}
        exceptions_set.add(lemma)
        self._exceptions_field.value = ", ".join(pali_list_sorter(exceptions_set))
        self._exceptions_field.update()
        self._focus_after_rebuild = row_idx
        if self._current_rule_key:
            self._on_update(None)

    # ── Results table ─────────────────────────────────────────────────────────

    def _on_save_changes(self, e: ft.ControlEvent) -> None:
        if not self._modified_cells:
            show_global_snackbar(self.page, "No changes to save", "info", 3000)
            return

        changes_by_row: dict[int, dict[str, str]] = {}
        for (row_idx, col_name), value in self._modified_cells.items():
            changes_by_row.setdefault(row_idx, {})[col_name] = value

        try:
            for row_idx, changes in changes_by_row.items():
                record = self._search_results[row_idx]
                for col_name, value in changes.items():
                    setattr(record, col_name, value)
                success, error = self.toolkit.db_manager.update_word_in_db(record)
                if not success:
                    show_global_snackbar(
                        self.page,
                        f"Failed to save row {row_idx + 1}: {error}",
                        "error",
                        5000,
                    )
                    self.toolkit.db_manager.db_session.rollback()
                    return

            self._modified_cells.clear()
            show_global_snackbar(
                self.page,
                f"Saved {len(changes_by_row)} record(s)",
                "info",
                4000,
            )
            self._on_wrong(None)
        except Exception as ex:
            self.toolkit.db_manager.db_session.rollback()
            show_global_snackbar(self.page, f"Error saving: {ex}", "error", 5000)

    def _update_results_table(self, results: list[DpdHeadword]) -> None:
        self._search_results = results
        self._modified_cells.clear()
        self._results_table.columns = (
            [
                ft.DataColumn(label=ft.Text("#", width=40)),
            ]
            + [
                ft.DataColumn(label=ft.Text(col, width=w))
                for col, w in zip(DISPLAY_COLUMNS, COLUMN_WIDTHS)
            ]
            + [
                ft.DataColumn(label=ft.Text("bold", width=100)),
                ft.DataColumn(label=ft.Text("e")),
            ]
        )

        rule_type = self._get_type_string()
        rows = []
        for idx, hw in enumerate(results):

            def make_tracker(row_idx: int, col: str):
                def on_change(e: ft.ControlEvent) -> None:
                    self._modified_cells[(row_idx, col)] = e.control.value or ""

                return on_change

            def make_cell(value: str, row_idx: int, col: str) -> CellTextField:
                field = CellTextField(value)
                field.on_change = make_tracker(row_idx, col)
                return field

            def make_autofill(
                field: CellTextField, default_val: str, row_idx: int, col: str
            ):
                def on_submit(e: ft.ControlEvent) -> None:
                    if not (field.value or "").strip():
                        field.value = default_val
                        field.update()
                        self._modified_cells[(row_idx, col)] = default_val
                    field.focus()

                return on_submit

            type_cell = make_cell(str(hw.compound_type or ""), idx, "compound_type")
            type_cell.multiline = False
            type_cell.on_submit = make_autofill(
                type_cell, rule_type, idx, "compound_type"
            )

            construction_cell = make_cell(
                str(hw.compound_construction or ""), idx, "compound_construction"
            )
            construction_cell.multiline = False
            construction_cell.on_submit = make_autofill(
                construction_cell,
                str(hw.lemma_clean or ""),
                idx,
                "compound_construction",
            )

            cells = [
                ft.DataCell(ft.Text(str(idx + 1), size=12)),
                ft.DataCell(make_cell(str(hw.lemma_1 or ""), idx, "lemma_1")),
                ft.DataCell(make_cell(str(hw.pos or ""), idx, "pos")),
                ft.DataCell(make_cell(str(hw.meaning_1 or ""), idx, "meaning_1")),
                ft.DataCell(type_cell),
                ft.DataCell(construction_cell),
                ft.DataCell(self._make_bold_field(construction_cell, idx)),
                ft.DataCell(self._make_exception_button(str(hw.lemma_1 or ""), idx)),
            ]
            rows.append(ft.DataRow(cells=cells))

        self._results_table.rows = rows
        self._results_table.update()

        # After exception add, focus the first editable cell of the same row
        # (which is now the next word since the excepted word was removed)
        if self._focus_after_rebuild >= 0 and rows:
            focus_idx = min(self._focus_after_rebuild, len(rows) - 1)
            # cells[1] is the lemma_1 CellTextField (cells[0] is the row number)
            first_cell = rows[focus_idx].cells[1].content
            if isinstance(first_cell, CellTextField):
                first_cell.focus()
            self._focus_after_rebuild = -1

    def _make_bold_field(
        self, construction_cell: CellTextField, row_idx: int
    ) -> ft.TextField:
        def on_submit(e: ft.ControlEvent) -> None:
            bold_text = e.control.value
            current = construction_cell.value or ""
            if not bold_text or not current:
                return
            new_value = re.sub(
                re.escape(bold_text) + r"(?=\s\+)",
                f"<b>{bold_text}</b>",
                current,
                count=1,
            )
            if new_value == current:
                new_value = re.sub(
                    re.escape(bold_text), f"<b>{bold_text}</b>", current, count=1
                )
            if new_value != current:
                construction_cell.value = new_value
                construction_cell.update()
                self._modified_cells[(row_idx, "compound_construction")] = new_value
            e.control.value = ""
            e.control.update()
            e.control.focus()

        return ft.TextField(
            hint_text="bold",
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            dense=True,
            text_size=12,
            border_radius=10,
            on_submit=on_submit,
        )

    def _make_exception_button(self, lemma: str, row_idx: int) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icons.BLOCK,
            icon_size=14,
            on_click=lambda e, lm=lemma, ri=row_idx: self._on_exception_add(lm, ri),
            style=ft.ButtonStyle(padding=ft.padding.all(0)),
            width=24,
            height=24,
        )
