# -*- coding: utf-8 -*-
"""Infl tab — editor for the inflection template TSV files.

Loads, edits, copies, renames and deletes inflection templates, and lists
the words that use the loaded pattern. The file work lives in
db/inflections/inflection_template_files.py, the db sync in
db/inflections/create_inflection_templates.py; this view is the Flet front
end. Layout: symmetrical and rigid, like a spreadsheet (spec §3).
"""

import re
from dataclasses import replace

import flet as ft

from db.inflections.inflection_template_files import (
    TemplateFile,
    load_templates,
    remove_template,
    rename_template,
    write_template,
)
from gui2.filter_component import FilterComponent
from gui2.toolkit import ToolKit
from gui2.ui_utils import field_border, is_mounted, request_focus
from tools.pali_sort_key import pali_list_sorter, pali_sort_key

# Every column is as wide as its longest text, never below these small
# minimums, so nothing wraps and nothing takes more room than it needs.
# *_CHAR_WIDTH is pixels per character, measured on the screen from wrapped
# boxes: forms are size 13 text (wide letters like m and y take about 11 px),
# headings are size 13 too but short and plain, grammar and row labels are
# size 12 grey text. BOX_PADDING covers a Flet text box's padding and border;
# 24 was too little and wrapped "imp 3rd sg".
FORMS_CHAR_WIDTH = 11
HEADING_CHAR_WIDTH = 10
GRAMMAR_CHAR_WIDTH = 9
BOX_PADDING = 36
LABEL_MIN_WIDTH = 70
FORMS_MIN_WIDTH = 70
GRAMMAR_MIN_WIDTH = 70
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200
BUTTON_WIDTH = 180
SHAPE_BUTTON_WIDTH = 110
FORM_LINE_SEPARATOR = "\n"


# ── module-level pure helpers (no Flet) ───────────────────────────────────


def grid_values_to_data(
    headings: list[str], rows: list[list[str]]
) -> list[list[list[str]]]:
    """Grid control values → template data.

    Forms are trimmed, blank lines dropped and sorted with
    pali_list_sorter; a cell with no forms is saved empty ([""]).
    Row 0 is [[""], heading, [""], heading, ...]; rows 1+ are
    [label, forms, grammar, ...].
    """
    data: list[list[list[str]]] = [[[""]]]
    for heading in headings:
        data[0].append([heading.strip()])
        data[0].append([""])

    for row in rows:
        new_row: list[list[str]] = [[" ".join(row[0].split())]]
        for cell_no in range(1, len(row), 2):
            forms = [line.strip() for line in row[cell_no].splitlines()]
            forms = pali_list_sorter([f for f in forms if f])
            new_row.append(forms if forms else [""])
            # grammar boxes are multi-line to match the row height; a newline
            # here would split the TSV line
            grammar = (
                " ".join(row[cell_no + 1].split()) if cell_no + 1 < len(row) else ""
            )
            new_row.append([grammar])
        data.append(new_row)
    return data


def data_to_grid_values(
    data: list[list[list[str]]],
) -> tuple[list[str], list[list[str]]]:
    """Template data → grid control values (the reverse of
    grid_values_to_data). Forms are one per line."""
    headings = [data[0][cell_no][0] for cell_no in range(1, len(data[0]), 2)]
    rows: list[list[str]] = []
    for row in data[1:]:
        grid_row = [row[0][0]]
        for cell_no in range(1, len(row), 2):
            forms = [form for form in row[cell_no] if form]
            grid_row.append(FORM_LINE_SEPARATOR.join(forms))
            grid_row.append(row[cell_no + 1][0])
        rows.append(grid_row)
    return headings, rows


def max_form_count(data: list[list[list[str]]]) -> int:
    """The largest number of forms in any cell (minimum 1)."""
    maximum = 1
    for row in data:
        for cell in row:
            maximum = max(maximum, len(cell))
    return maximum


def grid_dimensions(
    headings: list[str], rows: list[list[str]]
) -> tuple[int, list[int], list[int], list[int]]:
    """(label width, forms widths, grammar widths, line counts) for the grid.

    Every box is as wide as the widest box in its column and as tall as the
    tallest box in its row, so the grid stays rigid and nothing wraps. Widths
    are in pixels: one for the row-label column, then one forms width and one
    grammar width per column. Line counts are one per row (the rows after the
    heading row), at least 2 so a second form can always be typed."""
    label_width = max(
        [LABEL_MIN_WIDTH]
        + [len(row[0].strip()) * GRAMMAR_CHAR_WIDTH + BOX_PADDING for row in rows]
    )
    forms_widths = [
        max(FORMS_MIN_WIDTH, len(h.strip()) * HEADING_CHAR_WIDTH + BOX_PADDING)
        for h in headings
    ]
    grammar_widths = [GRAMMAR_MIN_WIDTH] * len(headings)
    line_counts: list[int] = []
    for row in rows:
        lines = 2
        for c in range(len(headings)):
            forms_no = 2 * c + 1
            forms = [f.strip() for f in row[forms_no].splitlines() if f.strip()]
            lines = max(lines, len(forms))
            longest_form = max((len(f) for f in forms), default=0)
            forms_widths[c] = max(
                forms_widths[c], longest_form * FORMS_CHAR_WIDTH + BOX_PADDING
            )
            grammar_len = len(row[forms_no + 1].strip())
            grammar_widths[c] = max(
                grammar_widths[c], grammar_len * GRAMMAR_CHAR_WIDTH + BOX_PADDING
            )
        line_counts.append(lines)
    return label_width, forms_widths, grammar_widths, line_counts


def validate_new_name(name: str, existing_patterns: list[str]) -> str | None:
    """Refusals for a new pattern name, or None if it is acceptable."""
    name_clean = name.strip()
    if not name_clean:
        return "name is empty"
    if "/" in name_clean or "\t" in name_clean:
        return "name cannot contain '/' or tabs"
    if name_clean in existing_patterns:
        return f"'{name_clean}' already exists"
    return None


def validate_template(t: TemplateFile) -> str | None:
    """Save's checks (spec §3), or None if the template is acceptable."""
    if not t.pattern:
        return "no pattern loaded"
    if not t.like:
        return "like is empty"
    for row in t.data:
        for cell in row:
            for form in cell:
                if "," in form:
                    return f"'{form}' contains a comma"
                if "\t" in form:
                    return f"'{form}' contains a tab"
    for cell_no, cell in enumerate(t.data[0]):
        if cell_no % 2 == 1 and cell == [""]:
            return "column heading is empty"
    for row in t.data[1:]:
        if row[0] == [""]:
            return "row label is empty"
    return None


def copy_template_core(
    t: TemplateFile, new_name: str, existing_patterns: list[str]
) -> tuple[TemplateFile | None, str]:
    """The non-Flet core of Copy: (new template, refusal message)."""
    refusal = validate_new_name(new_name, existing_patterns)
    if refusal:
        return None, refusal
    return replace(t, pattern=new_name.strip()), ""


def save_template_core(
    t: TemplateFile,
    index_path,
    templates_dir,
    existing_patterns: list[str],
) -> str:
    """The non-Flet core of Save: refusal message, "" on success."""
    refusal = validate_template(t)
    if refusal:
        return refusal
    if t.pattern not in existing_patterns:
        # an unsaved copy, or a file that appeared in the meantime
        refusal = validate_new_name(t.pattern, existing_patterns)
        if refusal:
            return refusal
    write_template(t, index_path, templates_dir)
    return ""


def rename_template_core(
    old: str,
    new: str,
    index_path,
    templates_dir,
    existing_patterns: list[str],
) -> str:
    """The non-Flet core of Rename: refusal message, "" on success."""
    new = new.strip()
    refusal = validate_new_name(new, existing_patterns)
    if refusal:
        return refusal
    rename_template(old, new, index_path, templates_dir)
    return ""


def delete_template_core(
    pattern: str,
    index_path,
    templates_dir,
    word_count: int,
) -> str:
    """The non-Flet core of Delete: refusal message, "" on success."""
    if word_count > 0:
        return f"{word_count} words use this pattern"
    remove_template(pattern, index_path, templates_dir)
    return ""


def pattern_word_filter(pattern: str) -> list[tuple[str, str]]:
    """Data filters selecting exactly the words with this pattern.

    build_filter_conditions uses regexp_match, so the ^…$ anchors keep
    'a nt' from also matching 'a nt irreg'."""
    return [("pattern", f"^{re.escape(pattern)}$")]


# ── the view ──────────────────────────────────────────────────────────────


class InflectionTemplatesTabView(ft.Column):
    """Full CRUD editor for the inflection template TSV files."""

    def __init__(self, page: ft.Page, toolkit: ToolKit) -> None:
        super().__init__(expand=True, spacing=5, controls=[])

        self.toolkit = toolkit
        self._db = toolkit.db_manager

        self._template: TemplateFile | None = None
        self._unsaved_copy_of: str | None = None
        # grid values: one string per cell, forms multi-line
        self._headings: list[str] = [""]
        self._rows: list[list[str]] = [["", "", ""]]
        self._shown_dims: tuple[int, list[int], list[int], list[int]] = (
            0,
            [],
            [],
            [],
        )
        self._words_shown: bool = False
        self._pattern_text: str = ""
        self._like_text: str = ""

        self._build_ui()

    def on_tab_focus(self) -> None:
        """Called by the app when this tab is opened: the pattern box takes
        the cursor, so you can type to find a pattern straight away."""
        if is_mounted(self._pattern_dropdown):
            request_focus(self._pattern_dropdown)

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        top = self._build_top_section()
        grid = self._build_grid_section()
        shapes = self._build_shape_buttons()
        bottom = self._build_bottom_section()
        self._filter_container = ft.Container(expand=True, visible=False)
        self.controls = [
            top,
            ft.Column(
                controls=[grid, shapes],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                spacing=5,
            ),
            bottom,
            self._filter_container,
        ]
        self._rebuild_grid()

    def _build_top_section(self) -> ft.Container:
        # first: building the dropdown's options can report a load error
        # through the message box
        self._message_field = ft.TextField(
            "",
            read_only=True,
            multiline=True,
            min_lines=1,
            max_lines=4,
            expand=True,
            border=field_border(color=HIGHLIGHT_COLOUR),
            color=HIGHLIGHT_COLOUR,
            hint_text="Messages",
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            text_size=14,
        )

        self._pattern_dropdown = ft.Dropdown(
            hint_text="Select pattern",
            hint_style=ft.TextStyle(color=LABEL_COLOUR),
            options=self._dropdown_options(),
            editable=True,
            enable_filter=True,
            enable_search=True,
            expand=True,
            border=field_border(color=ft.Colors.GREY_800),
            text_size=14,
            on_select=self._on_dropdown_change,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._pattern_dropdown,
                            ft.Button(
                                "Copy", on_click=self._copy_template, width=BUTTON_WIDTH
                            ),
                            ft.Button(
                                "Rename",
                                on_click=self._rename_template,
                                width=BUTTON_WIDTH,
                            ),
                            ft.Button(
                                "Clear", on_click=self._clear_all, width=BUTTON_WIDTH
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(controls=[self._message_field]),
                ],
                spacing=8,
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
        )

    def _set_pattern_text(self, value: str) -> None:
        """The pattern and like boxes are new controls on every grid rebuild
        (a control kept across rebuilds is a moved control, which Flet's diff
        does not handle), so their text lives here, not in the boxes."""
        self._pattern_text = value
        self._pattern_field.value = value

    def _set_like_text(self, value: str) -> None:
        self._like_text = value
        self._like_field.value = value

    def _on_like_change(self, e: ft.ControlEvent) -> None:
        self._like_text = e.control.value or ""

    def _build_grid_section(self) -> ft.Row:
        # one place in the tree; shape changes rebuild only its controls
        self._grid_column = ft.Column(controls=[], spacing=1)
        return ft.Row(
            controls=[self._grid_column],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

    def _build_shape_buttons(self) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Button(
                    "+ row",
                    on_click=self._add_row,
                    width=SHAPE_BUTTON_WIDTH,
                ),
                ft.Button(
                    "− row",
                    on_click=self._remove_last_row,
                    width=SHAPE_BUTTON_WIDTH,
                ),
                ft.Button(
                    "+ col",
                    on_click=self._add_column,
                    width=SHAPE_BUTTON_WIDTH,
                ),
                ft.Button(
                    "− col",
                    on_click=self._remove_last_column,
                    width=SHAPE_BUTTON_WIDTH,
                ),
            ],
            spacing=10,
        )

    def _build_bottom_section(self) -> ft.Container:
        self._words_button = ft.Button(
            "Show words", on_click=self._toggle_words, width=BUTTON_WIDTH
        )
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Button("Save", on_click=self._save_template, width=BUTTON_WIDTH),
                    ft.Button(
                        "Delete",
                        on_click=self._delete_template,
                        width=BUTTON_WIDTH,
                    ),
                    self._words_button,
                ],
                spacing=10,
            ),
            padding=ft.Padding.all(10),
        )

    def _grey_label(self, text: str, width: int) -> ft.Container:
        """A grey right-aligned label in a cell of the given width."""
        return ft.Container(
            width=width,
            alignment=ft.Alignment.CENTER_RIGHT,
            padding=ft.Padding.only(right=10),
            content=ft.Text(text, color=LABEL_COLOUR, size=12),
        )

    # ── grid building ─────────────────────────────────────────────────────

    def _column_count(self) -> int:
        return len(self._headings)

    def _make_box(
        self,
        value: str,
        width: int,
        line_count: int,
        grey: bool = False,
        read_only: bool = False,
        right_align: bool = False,
        on_change=None,
        on_blur=None,
        multiline: bool = False,
        heading: bool = False,
    ) -> ft.TextField:
        return ft.TextField(
            value=value,
            width=width,
            multiline=multiline,
            min_lines=line_count,
            max_lines=line_count,
            on_blur=on_blur,
            read_only=read_only,
            # headings (the column headings and the row titles) are blue,
            # everything else is data
            border=field_border(color=HIGHLIGHT_COLOUR if heading else None),
            text_size=12 if grey else 13,
            color=HIGHLIGHT_COLOUR
            if heading
            else (LABEL_COLOUR if grey else ft.Colors.WHITE),
            text_align=ft.TextAlign.RIGHT if right_align else ft.TextAlign.LEFT,
            content_padding=ft.Padding.symmetric(horizontal=6, vertical=4),
            on_change=on_change,
        )

    def _rebuild_grid(self) -> None:
        label_width, forms_widths, grammar_widths, line_counts = grid_dimensions(
            self._headings, self._rows
        )
        # the pattern box sits over the first forms column and the like box
        # over the second, so those columns also fit those two texts
        forms_widths[0] = max(
            forms_widths[0], len(self._pattern_text) * FORMS_CHAR_WIDTH + BOX_PADDING
        )
        if len(forms_widths) > 1:
            forms_widths[1] = max(
                forms_widths[1], len(self._like_text) * FORMS_CHAR_WIDTH + BOX_PADDING
            )
        self._shown_dims = (label_width, forms_widths, grammar_widths, line_counts)

        # pattern sits over the first forms column and like over the second,
        # each with its label in the cell to its left
        self._pattern_field = ft.TextField(
            value=self._pattern_text,
            read_only=True,
            width=forms_widths[0],
            border=field_border(),
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        )
        self._like_field = ft.TextField(
            value=self._like_text,
            width=forms_widths[1] if len(forms_widths) > 1 else FORMS_MIN_WIDTH,
            border=field_border(),
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            on_change=self._on_like_change,
        )
        fields_row = ft.Row(
            controls=[
                self._grey_label("pattern", label_width),
                self._pattern_field,
                self._grey_label("like", grammar_widths[0]),
                self._like_field,
            ],
            spacing=1,
        )

        header_controls: list[ft.Control] = [ft.Container(width=label_width)]
        for c, heading in enumerate(self._headings):
            header_controls.append(
                self._make_box(
                    heading,
                    forms_widths[c],
                    1,
                    heading=True,
                    on_change=lambda e, c=c: self._on_heading_change(c, e),
                )
            )
            header_controls.append(ft.Container(width=grammar_widths[c]))

        grid_rows: list[ft.Control] = [
            fields_row,
            ft.Row(controls=header_controls, spacing=1),
        ]
        for r, row in enumerate(self._rows):
            row_controls: list[ft.Control] = [
                self._make_box(
                    row[0],
                    label_width,
                    line_counts[r],
                    grey=True,
                    heading=True,
                    right_align=True,
                    multiline=True,
                    on_change=lambda e, r=r: self._on_cell_change(r, 0, e),
                )
            ]
            for c in range(self._column_count()):
                forms_no = 2 * c + 1
                row_controls.append(
                    self._make_box(
                        row[forms_no],
                        forms_widths[c],
                        line_counts[r],
                        multiline=True,
                        on_change=lambda e, r=r, n=forms_no: self._on_cell_change(
                            r, n, e
                        ),
                        on_blur=lambda e: self._on_forms_blur(),
                    )
                )
                grammar_no = forms_no + 1
                row_controls.append(
                    self._make_box(
                        row[grammar_no],
                        grammar_widths[c],
                        line_counts[r],
                        multiline=True,
                        grey=True,
                        on_change=lambda e, r=r, n=grammar_no: self._on_cell_change(
                            r, n, e
                        ),
                        on_blur=lambda e: self._on_forms_blur(),
                    )
                )
            grid_rows.append(
                ft.Row(
                    controls=row_controls,
                    spacing=1,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            )

        self._grid_column.controls = grid_rows
        if is_mounted(self):
            self.page.update()

    # ── data ↔ grid ───────────────────────────────────────────────────────

    def _load_grid_from_template(self, t: TemplateFile) -> None:
        self._headings, self._rows = data_to_grid_values(t.data)
        self._rebuild_grid()

    def _build_template_from_grid(self, name: str) -> TemplateFile:
        like = self._like_text.strip()
        data = grid_values_to_data(self._headings, self._rows)
        return TemplateFile(pattern=name, like=like, data=data)

    # ── file + dropdown helpers ───────────────────────────────────────────

    def _get_templates(self) -> list[TemplateFile]:
        try:
            return load_templates(
                self._db.pth.inflection_templates_index_path,
                self._db.pth.inflection_templates_dir,
            )
        except ValueError as e:
            self._set_message(str(e))
            return []

    def _existing_patterns_or_none(self) -> list[str] | None:
        """All pattern names, or None (with a message) when the files do not
        load. A failed load must stop Copy, Rename and Save: an empty list
        would make every name look free and let a save overwrite a template."""
        try:
            templates = load_templates(
                self._db.pth.inflection_templates_index_path,
                self._db.pth.inflection_templates_dir,
            )
        except ValueError as e:
            self._set_message(f"template files do not load: {e}")
            return None
        return [t.pattern for t in templates]

    def _dropdown_options(self) -> list[ft.dropdown.Option]:
        patterns = [t.pattern for t in self._get_templates()]
        return [ft.dropdown.Option(p) for p in sorted(patterns, key=pali_sort_key)]

    def _refresh_dropdown(self, selected: str | None = None) -> None:
        self._pattern_dropdown.options = self._dropdown_options()
        self._pattern_dropdown.value = selected
        if is_mounted(self):
            self.page.update()

    # ── word list ─────────────────────────────────────────────────────────

    def set_word_list(self, pattern: str | None) -> None:
        """Show the words using this pattern, or nothing for None."""
        self._filter_container.visible = pattern is not None
        if pattern is None:
            self._filter_container.content = None
        else:
            self._filter_container.content = FilterComponent(
                page=self.page,
                toolkit=self.toolkit,
                data_filters=pattern_word_filter(pattern),
                display_filters=[
                    "id",
                    "lemma_1",
                    "pos",
                    "stem",
                    "pattern",
                    "meaning_1",
                ],
            )
        if is_mounted(self):
            self.page.update()

    def _toggle_words(self, e: ft.ControlEvent) -> None:
        """Show or hide the words using the loaded pattern. The list is built
        only when asked for: it costs a database query and screen space."""
        if self._template is None or self._unsaved_copy_of is not None:
            self._set_message("load a saved pattern first")
            return
        self._words_shown = not self._words_shown
        self._refresh_words()

    def _refresh_words(self) -> None:
        """Bring the word list and its button in line with the flag."""
        pattern = self._template.pattern if self._template else None
        shown = self._words_shown and pattern is not None
        self._words_button.content = "Hide words" if shown else "Show words"
        self.set_word_list(pattern if shown else None)

    # ── event handlers ────────────────────────────────────────────────────

    def _on_dropdown_change(self, e: ft.ControlEvent) -> None:
        selected = self._pattern_dropdown.value
        if selected:
            self._load_template(selected)

    def _on_heading_change(self, c: int, e: ft.ControlEvent) -> None:
        self._headings[c] = e.control.value or ""

    def _on_cell_change(self, r: int, n: int, e: ft.ControlEvent) -> None:
        self._rows[r][n] = e.control.value or ""

    def _on_forms_blur(self) -> None:
        """Grow the grid when a box now needs more room than it has. Done on
        blur, not per key: a rebuild drops the focus."""
        label_width, forms_widths, grammar_widths, line_counts = grid_dimensions(
            self._headings, self._rows
        )
        shown_label, shown_forms, shown_grammar, shown_lines = self._shown_dims
        if (
            label_width > shown_label
            or any(n > o for n, o in zip(forms_widths, shown_forms))
            or any(n > o for n, o in zip(grammar_widths, shown_grammar))
            or any(n > o for n, o in zip(line_counts, shown_lines))
        ):
            self._rebuild_grid()

    def _add_row(self, e: ft.ControlEvent) -> None:
        self._rows.append([""] * (2 * self._column_count() + 1))
        self._rebuild_grid()

    def _remove_last_row(self, e: ft.ControlEvent) -> None:
        if len(self._rows) <= 1:
            self._set_message("the grid needs at least one row")
            return
        self._rows.pop()
        self._rebuild_grid()

    def _add_column(self, e: ft.ControlEvent) -> None:
        self._headings.append("")
        for row in self._rows:
            row.extend(["", ""])
        self._rebuild_grid()

    def _remove_last_column(self, e: ft.ControlEvent) -> None:
        if self._column_count() <= 1:
            self._set_message("the grid needs at least one column")
            return
        self._headings.pop()
        for row in self._rows:
            del row[-2:]
        self._rebuild_grid()

    # ── CRUD ──────────────────────────────────────────────────────────────

    def _load_template(self, pattern: str) -> None:
        t = next((x for x in self._get_templates() if x.pattern == pattern), None)
        if t is None:
            self._set_message(f"'{pattern}' not found")
            return

        self._template = t
        self._unsaved_copy_of = None
        self._set_pattern_text(t.pattern)
        self._set_like_text(t.like)
        self._load_grid_from_template(t)
        self._words_shown = False
        self._refresh_words()
        self._set_message(f"Loaded: {t.pattern}")

    def _copy_template(self, e: ft.ControlEvent) -> None:
        if self._template is None:
            self._set_message("load a pattern first")
            return
        self._show_name_dialog(
            "Copy pattern",
            self._template.pattern,
            self._on_copy_ok,
        )

    def _on_copy_ok(self, new_name: str) -> str | None:
        """Dialog OK for Copy. Returns a refusal to keep the dialog open."""
        if self._template is None:
            return "no pattern loaded"
        existing = self._existing_patterns_or_none()
        if existing is None:
            return "template files do not load"
        new_t, refusal = copy_template_core(self._template, new_name, existing)
        if new_t is None:
            return refusal

        old = self._template.pattern
        self._template = new_t
        self._unsaved_copy_of = old
        self._set_pattern_text(new_t.pattern)
        self._words_shown = False
        self._refresh_words()
        self._set_message(f"copy of {old} — edit, then Save")
        return None

    def _rename_template(self, e: ft.ControlEvent) -> None:
        if self._template is None:
            self._set_message("no pattern loaded")
            return
        if self._unsaved_copy_of is not None:
            self._set_message("save the copy first, then rename it")
            return
        self._show_name_dialog(
            "Rename pattern",
            self._template.pattern,
            self._on_rename_ok,
        )

    def _on_rename_ok(self, new_name: str) -> str | None:
        """Dialog OK for Rename. Returns a refusal to keep the dialog open."""
        if self._template is None:
            return "no pattern loaded"
        old = self._template.pattern
        new_name = new_name.strip()
        existing = self._existing_patterns_or_none()
        if existing is None:
            return "template files do not load"
        index_path = self._db.pth.inflection_templates_index_path
        templates_dir = self._db.pth.inflection_templates_dir
        refusal = rename_template_core(
            old, new_name, index_path, templates_dir, existing
        )
        if refusal:
            return refusal

        # The files are renamed; if the db step fails, put everything back so
        # the files, the index and the words never disagree.
        count = 0
        try:
            count = self._db.rename_pattern_in_headwords(old, new_name)
            self._db.sync_inflection_templates()
        except Exception as ex:
            self._db.db_session.rollback()
            if count:
                self._db.rename_pattern_in_headwords(new_name, old)
            rename_template(new_name, old, index_path, templates_dir)
            return f"rename failed, nothing changed: {ex}"
        self._template.pattern = new_name
        self._set_pattern_text(new_name)
        self._refresh_dropdown(selected=new_name)
        self._refresh_words()
        self._set_message(
            f"renamed {old} → {new_name}, {count} words moved, "
            "press Update Inflections on the Global tab"
        )
        return None

    def _save_template(self, e: ft.ControlEvent) -> None:
        if self._template is None:
            self._set_message("no pattern loaded")
            return

        existing = self._existing_patterns_or_none()
        if existing is None:
            return
        name = self._pattern_text.strip()
        t = self._build_template_from_grid(name)
        refusal = save_template_core(
            t,
            self._db.pth.inflection_templates_index_path,
            self._db.pth.inflection_templates_dir,
            existing,
        )
        if refusal:
            self._set_message(refusal)
            return

        self._db.sync_inflection_templates()
        count = self._db.get_pattern_headword_count(name)
        # show what is now in the file: forms trimmed and sorted
        saved = next((x for x in self._get_templates() if x.pattern == name), t)
        self._template = saved
        self._unsaved_copy_of = None
        self._set_like_text(saved.like)
        self._load_grid_from_template(saved)
        self._refresh_dropdown(selected=name)
        self._refresh_words()
        self._set_message(
            f"saved, {count} words use it, press Update Inflections on the Global tab"
        )

    def _delete_template(self, e: ft.ControlEvent) -> None:
        if self._template is None:
            self._set_message("no pattern loaded")
            return
        if self._unsaved_copy_of is not None:
            self._set_message("save the copy first, then delete it")
            return

        pattern = self._template.pattern
        count = self._db.get_pattern_headword_count(pattern)
        if count > 0:
            self._set_message(f"{count} words use this pattern")
            return

        self._show_delete_confirm(pattern)

    def _on_delete_ok(self, pattern: str) -> None:
        # the files go only after the confirm; the count is read again in case
        # a word took the pattern while the dialog was open
        refusal = delete_template_core(
            pattern,
            self._db.pth.inflection_templates_index_path,
            self._db.pth.inflection_templates_dir,
            self._db.get_pattern_headword_count(pattern),
        )
        if refusal:
            self._set_message(refusal)
            return
        self._db.sync_inflection_templates()
        self._clear_all()
        self._refresh_dropdown()
        self._set_message(f"deleted: {pattern}")

    def _clear_all(self, e: ft.ControlEvent | None = None) -> None:
        self._template = None
        self._unsaved_copy_of = None
        self._headings = [""]
        self._rows = [["", "", ""]]
        self._pattern_dropdown.value = None
        self._set_pattern_text("")
        self._set_like_text("")
        self._rebuild_grid()
        self._words_shown = False
        self._refresh_words()
        self._set_message("")
        if is_mounted(self):
            self.page.update()

    # ── dialogs ───────────────────────────────────────────────────────────

    def _show_name_dialog(self, title: str, initial: str, on_ok) -> None:
        """A name box with OK and Cancel. OK's refusal is shown inside the
        dialog and keeps it open."""
        name_field = ft.TextField(
            value=initial,
            border=field_border(),
            text_size=14,
            autofocus=True,
        )
        error_text = ft.Text("", color=ft.Colors.RED, size=12)

        def ok(e: ft.ControlEvent) -> None:
            refusal = on_ok(name_field.value or "")
            if refusal:
                error_text.value = refusal
                self.page.update()
            else:
                self.page.pop_dialog()

        def cancel(e: ft.ControlEvent) -> None:
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Column(
                controls=[name_field, error_text],
                tight=True,
            ),
            actions=[
                ft.TextButton("OK", on_click=ok),
                ft.TextButton("Cancel", on_click=cancel),
            ],
        )
        self.page.show_dialog(dlg)

    def _show_delete_confirm(self, pattern: str) -> None:
        def confirm(e: ft.ControlEvent) -> None:
            self.page.pop_dialog()
            self._on_delete_ok(pattern)

        def cancel(e: ft.ControlEvent) -> None:
            self.page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Delete '{pattern}'? No words use it."),
            actions=[
                ft.TextButton("Delete", on_click=confirm),
                ft.TextButton("Cancel", on_click=cancel),
            ],
        )
        self.page.show_dialog(dlg)

    # ── internal helpers ──────────────────────────────────────────────────

    def _set_message(self, msg: str) -> None:
        self._message_field.value = msg
        if is_mounted(self):
            self._message_field.update()
