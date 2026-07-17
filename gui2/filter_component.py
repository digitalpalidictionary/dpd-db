import re
import threading

import flet as ft

from db.models import DpdHeadword
from gui2.filter_logic import (
    build_filter_conditions,
    cell_value_str,
    clamp_page_index,
    compute_column_widths,
    effective_total,
    group_changes_by_id,
    page_label,
    track_cell_change,
    validate_regex_patterns,
)
from gui2.toolkit import ToolKit
from gui2.ui_utils import show_global_snackbar
from tools.spelling import CustomSpellChecker

PAGE_SIZE = 100
SPELL_CHECK_COLUMNS = ("meaning_1", "meaning_lit", "meaning_2")


class DpdDatatable(ft.DataTable):
    def __init__(self, columns, rows):
        super().__init__(
            columns=columns,
            rows=rows,
            data_text_style=ft.TextStyle(size=12, color=ft.Colors.GREY_300),
            border=ft.border.all(2, ft.Colors.BLACK),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_900,
            column_spacing=20,
            horizontal_margin=10,
            heading_text_style=ft.TextStyle(
                color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12
            ),
            heading_row_height=30,
            data_row_min_height=30,
            data_row_max_height=float("inf"),
            show_checkbox_column=False,
        )


class ColumnText(ft.Text):
    def __init__(self, text, width):
        super().__init__(
            value=text,
            expand=True,
            width=width,
            show_selection_cursor=True,
        )


CELL_PADDING = 4


class CellText(ft.Container):
    """Read-only cell content. Tapping the cell swaps in a CellTextField."""

    def __init__(self, text: str, width: int, misspelled: bool = False):
        super().__init__(
            content=ft.Text(
                value=text,
                size=12,
                color=ft.Colors.RED if misspelled else ft.Colors.GREY_300,
            ),
            width=width,
            padding=ft.padding.all(CELL_PADDING),
        )


class CellTextField(ft.TextField):
    """Editable cell content, sized to match the CellText it replaces so the
    row keeps the same spacing while editing."""

    def __init__(self, text: str, width: float | None = None):
        super().__init__(
            value=text,
            width=width,
            multiline=True,
            dense=True,
            content_padding=ft.padding.all(CELL_PADDING),
            border_radius=0,
            border=ft.InputBorder.OUTLINE,
            border_width=3,
            border_color=ft.Colors.TRANSPARENT,
            text_align=ft.TextAlign.LEFT,
            text_style=ft.TextStyle(
                size=12,
                color=ft.Colors.GREY_300,
            ),
        )


class FilterComponent(ft.Column):
    """A modular filter component for DPD database filtering."""

    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
        data_filters: list[tuple[str, str]] | None = None,
        display_filters: list[str] | None = None,
        limit: int | None = None,
        sort_column: str | None = None,
    ) -> None:
        super().__init__(expand=True, spacing=5, controls=[])
        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit
        self.spellchecker = CustomSpellChecker()

        # State management
        self.filtered_results: list[DpdHeadword] = []
        self.dpd_headword_columns = [c.name for c in DpdHeadword.__table__.columns]
        self.display_filters = display_filters
        self.data_filters = data_filters
        self.limit = limit
        self.sort_column = sort_column or "lemma_1"

        # Pagination state
        self.page_index: int = 0
        self.page_offset: int = 0
        self._apply_generation: int = 0
        self._apply_lock = threading.Lock()

        # Change tracking: {(headword_id, column_name): new_value} — keyed by
        # id, not row index, so a re-queried/reordered table can't misdirect
        # a pending edit.
        self.modified_cells: dict[tuple[int, str], str] = {}

        # UI Controls
        self.results_table: ft.DataTable | None = None
        self.progress_ring = ft.ProgressRing(width=24, height=24, visible=True)
        self.prev_page_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            on_click=self._prev_page_clicked,
            disabled=True,
            tooltip="Previous page",
        )
        self.next_page_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            on_click=self._next_page_clicked,
            disabled=True,
            tooltip="Next page",
        )
        self.page_label_text = ft.Text("", size=12)

        self._build_ui()

    def did_mount(self) -> None:
        """Run the first query once the component is on the page, off the
        UI thread, so the tab paints (with a progress ring) immediately."""
        self._start_apply()

    def _build_ui(self) -> None:
        """Build the main UI structure for the filter component."""
        results_section = self._create_results_section()

        self.controls.extend(
            [
                results_section,
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ElevatedButton(
                                "Save Changes", on_click=self._save_changes
                            ),
                            self.prev_page_button,
                            self.page_label_text,
                            self.next_page_button,
                            self.progress_ring,
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                ),
            ]
        )

    def _create_results_section(self) -> ft.Column:
        """Create the results display section."""

        # Create a placeholder column to avoid the AssertionError
        placeholder_column = ft.DataColumn(label=ft.Text("ID"))

        self.results_table = DpdDatatable(
            columns=[placeholder_column],
            rows=[],
        )

        # Wrap in containers for proper scrolling
        table_container = ft.Container(
            content=self.results_table,
        )

        # Horizontal scroll for wide tables
        horizontal_scroll = ft.Row(
            [table_container],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            alignment=ft.MainAxisAlignment.START,
        )

        # Vertical scroll for tall tables
        scrollable_table_container = ft.Column(
            [horizontal_scroll],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        return ft.Column(
            [scrollable_table_container],
            expand=True,
        )

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            if self.page:
                self.page.update()

    # --- APPLY FILTERS (off the UI thread) ---

    def _start_apply(self) -> None:
        """Kick off a query+build run in a worker thread. A generation
        counter discards stale runs when a newer apply supersedes them."""
        with self._apply_lock:
            self._apply_generation += 1
            generation = self._apply_generation
        self.progress_ring.visible = True
        self.prev_page_button.disabled = True
        self.next_page_button.disabled = True
        self._safe_update()
        self.page.run_thread(self._apply_filters, generation)

    def _prev_page_clicked(self, e: ft.ControlEvent) -> None:
        self.page_index -= 1
        self._start_apply()

    def _next_page_clicked(self, e: ft.ControlEvent) -> None:
        self.page_index += 1
        self._start_apply()

    def _apply_filters(self, generation: int) -> None:
        """Query one page of results and rebuild the table."""
        try:
            data_filters = self.data_filters or []

            error_msg = validate_regex_patterns(data_filters)
            if error_msg:
                show_global_snackbar(self.page, error_msg, "error", 5000)
                self._finish_progress()
                return

            display_columns = (
                self.display_filters
                if self.display_filters
                else [column.name for column in DpdHeadword.__table__.columns]
            )

            result_limit = self.limit if self.limit is not None else 0

            conditions, error_msg = build_filter_conditions(data_filters)
            if error_msg:
                show_global_snackbar(self.page, error_msg, "error", 5000)
                self._finish_progress()
                return

            # One fresh session per apply, so edits committed by other
            # processes are visible.
            self.toolkit.db_manager.new_db_session()
            sort_column_attr = getattr(DpdHeadword, self.sort_column, DpdHeadword.id)
            query = (
                self.toolkit.db_manager.db_session.query(DpdHeadword)
                .filter(*conditions)
                # Secondary sort on id keeps paging stable when the sort
                # column has ties.
                .order_by(sort_column_attr, DpdHeadword.id)
            )

            total = effective_total(query.count(), result_limit)
            page_index = clamp_page_index(self.page_index, total, PAGE_SIZE)
            page_offset = page_index * PAGE_SIZE
            page_limit = min(PAGE_SIZE, total - page_offset)

            if page_limit > 0:
                results = query.offset(page_offset).limit(page_limit).all()
            else:
                results = []

            # Shared state and the table are only written by the current
            # generation, under the lock, so a superseded run can't clobber
            # a newer one's results mid-render.
            with self._apply_lock:
                if generation != self._apply_generation:
                    return

                self.page_index = page_index
                self.page_offset = page_offset
                self.filtered_results = results

                self._update_results_table(display_columns)

                self.page_label_text.value = page_label(page_index, PAGE_SIZE, total)
                self.prev_page_button.disabled = page_index <= 0
                self.next_page_button.disabled = (page_offset + PAGE_SIZE) >= total
                self.progress_ring.visible = False
                self._safe_update()

        except Exception as ex:
            error_msg = f"Error applying filters: {str(ex)}"
            show_global_snackbar(self.page, error_msg, "error", 5000)
            self._finish_progress()

    def _finish_progress(self) -> None:
        self.progress_ring.visible = False
        self._safe_update()

    # --- TABLE BUILD ---

    def _update_results_table(self, display_columns: list[str]) -> None:
        """Update the results table with filtered data."""

        if not hasattr(self, "results_table") or not self.results_table:
            return

        # Clear existing data
        self.results_table.columns = []
        self.results_table.rows = []

        # Handle case where no display columns are specified
        if not display_columns:
            # Add a default column to avoid the AssertionError
            self.results_table.columns.append(ft.DataColumn(label=ft.Text("ID")))
            return

        column_widths = compute_column_widths(self.filtered_results, display_columns)

        # Create columns
        self.results_table.columns.append(ft.DataColumn(label=ColumnText("#", 40)))
        for col_name in display_columns:
            width = column_widths.get(col_name, 150)  # Default width if no results
            self.results_table.columns.append(
                ft.DataColumn(label=ColumnText(col_name, width))
            )

        # Create rows: read-only Text cells; tapping a cell swaps in an
        # editable TextField (a TextField per cell is what froze the tab).
        for row_index, result in enumerate(self.filtered_results):
            cells = [
                ft.DataCell(CellText(str(self.page_offset + row_index + 1), width=40))
            ]

            for col_name in display_columns:
                value_str = cell_value_str(getattr(result, col_name, ""))
                width = column_widths.get(col_name, 150)

                misspelled = bool(
                    col_name in SPELL_CHECK_COLUMNS
                    and value_str
                    and self.spellchecker.has_misspellings(
                        re.sub(r"<[^>]+>", "", value_str)
                    )
                )
                cell = ft.DataCell(CellText(value_str, width, misspelled))

                if col_name != "id":
                    cell.on_tap = self._make_cell_tap_handler(
                        cell, result.id, col_name, value_str
                    )

                cells.append(cell)

            self.results_table.rows.append(
                ft.DataRow(
                    cells=cells,
                )
            )

    def _make_cell_tap_handler(
        self, cell: ft.DataCell, headword_id: int, col_name: str, original_value: str
    ):
        def on_tap(e: ft.ControlEvent) -> None:
            self._begin_cell_edit(cell, headword_id, col_name, original_value)

        return on_tap

    def _begin_cell_edit(
        self, cell: ft.DataCell, headword_id: int, col_name: str, original_value: str
    ) -> None:
        """Swap the read-only cell for an editable TextField."""
        cell_width = cell.content.width if isinstance(cell.content, CellText) else None
        text_field = CellTextField(original_value, cell_width)
        text_field.data = original_value

        def on_change(e: ft.ControlEvent) -> None:
            track_cell_change(
                self.modified_cells,
                (headword_id, col_name),
                e.control.value or "",
                original_value,
            )
            if col_name in SPELL_CHECK_COLUMNS:
                self._spell_check_cell(e)

        text_field.on_change = on_change

        if col_name in SPELL_CHECK_COLUMNS:
            self._check_and_set_spell_border(text_field, original_value)

        cell.content = text_field
        cell.on_tap = None
        self._safe_update()
        text_field.focus()

    # --- SAVE ---

    def _save_changes(self, e: ft.ControlEvent | None) -> None:
        """Save any changes back to the database: one commit for the whole
        batch, one relationship-detector invalidation."""
        if not self.modified_cells:
            show_global_snackbar(self.page, "No changes to save", "info", 3000)
            return

        for (_, col_name), value in self.modified_cells.items():
            if col_name in ("meaning_1", "meaning_lit") and value:
                misspelled = self.spellchecker.check_sentence(value)
                if misspelled:
                    error_string = ", ".join(misspelled.keys())
                    show_global_snackbar(
                        self.page,
                        f"spelling mistakes in {col_name}: {error_string}",
                        "error",
                        5000,
                    )
                    return

        db_session = self.toolkit.db_manager.db_session
        try:
            changes_by_id = group_changes_by_id(self.modified_cells)

            for headword_id, changes in changes_by_id.items():
                record = db_session.query(DpdHeadword).filter_by(id=headword_id).first()
                if record is None:
                    show_global_snackbar(
                        self.page,
                        f"Failed to save changes: id {headword_id} not found",
                        "error",
                        5000,
                    )
                    db_session.rollback()
                    return

                for col_name, value in changes.items():
                    setattr(record, col_name, value)

            db_session.commit()
            self.toolkit.db_manager.mark_corpus_stale()
            self.toolkit.db_manager.invalidate_relationship_detector()
            self.modified_cells.clear()
            self._start_apply()
            show_global_snackbar(
                self.page,
                f"Successfully saved {len(changes_by_id)} records",
                "info",
                4000,
            )

        except Exception as ex:
            db_session.rollback()
            show_global_snackbar(
                self.page, f"Error saving changes: {str(ex)}", "error", 5000
            )
            import traceback

            print(f"Full traceback: {traceback.format_exc()}")

    # --- SPELL CHECK ---

    def _check_and_set_spell_border(self, field: ft.TextField, value: str):
        if not value:
            field.border_color = ft.Colors.TRANSPARENT
            return

        clean_value = re.sub(r"<[^>]+>", "", value)

        if self.spellchecker.has_misspellings(clean_value):
            field.border_color = ft.Colors.RED
        else:
            field.border_color = ft.Colors.TRANSPARENT

    def _spell_check_cell(self, e: ft.ControlEvent) -> None:
        """Spell check cell content and update border."""
        self._check_and_set_spell_border(e.control, e.control.value)
        try:
            e.control.update()
        except Exception:
            if self.page:
                self.page.update()
