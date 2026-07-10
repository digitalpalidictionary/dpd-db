"""Pure logic extracted from filter_component.py so it can be tested
without a live flet.Page (findings F6)."""

import re

from sqlalchemy import ColumnElement

from db.models import DpdHeadword


def cell_value_str(value: object) -> str:
    """Convert a DpdHeadword column value to its display string."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def validate_regex_patterns(data_filters: list[tuple[str, str]]) -> str | None:
    """Return an error message for the first invalid regex, or None."""
    for i, (_, pattern) in enumerate(data_filters):
        try:
            re.compile(pattern)
        except re.error as ex:
            return f"Invalid regex pattern in filter {i + 1}: {str(ex)}"
    return None


def parse_id_filter(pattern: str) -> list[int] | None:
    """Extract IDs from a pattern like ^(1571|3106|4365)$.

    Returns None when the pattern is not in that shape or contains no
    valid integers — callers fall back to regexp matching.
    """
    match = re.match(r"^\^\(([^)]+)\)\$$", pattern)
    if not match:
        return None
    id_list = []
    for id_str in match.group(1).split("|"):
        try:
            id_list.append(int(id_str))
        except ValueError:
            pass
    return id_list or None


def build_filter_conditions(
    data_filters: list[tuple[str, str]],
) -> tuple[list[ColumnElement[bool]], str]:
    """Turn (column, pattern) pairs into SQLAlchemy filter conditions.

    Returns (conditions, "") on success or ([], error_message) when a
    column name does not exist on DpdHeadword.
    """
    conditions: list[ColumnElement[bool]] = []
    for column_name, pattern in data_filters:
        column_attr = getattr(DpdHeadword, column_name, None)
        if column_attr is None:
            return [], f"Column '{column_name}' not found in DpdHeadword"

        if column_name == "id":
            id_list = parse_id_filter(pattern)
            if id_list:
                conditions.append(column_attr.in_(id_list))
            else:
                conditions.append(column_attr.regexp_match(pattern))
        else:
            conditions.append(column_attr.regexp_match(pattern))
    return conditions, ""


def compute_column_widths(
    results: list[DpdHeadword], display_columns: list[str]
) -> dict[str, int]:
    """Width per column from the longest cell value, clamped to 120-500."""
    column_widths: dict[str, int] = {}
    if not results:
        return column_widths
    for col_name in display_columns:
        max_len = len(col_name)
        for result in results:
            value_str = cell_value_str(getattr(result, col_name, ""))
            max_len = max(max_len, len(value_str))
        column_widths[col_name] = max(120, min(max_len * 8, 500))
    return column_widths


def track_cell_change(
    modified_cells: dict[tuple[int, str], str],
    key: tuple[int, str],
    new_value: str,
    original_value: str,
) -> None:
    """Record a cell edit, or drop the record when reverted to original."""
    if new_value != original_value:
        modified_cells[key] = new_value
    elif key in modified_cells:
        del modified_cells[key]


def group_changes_by_id(
    modified_cells: dict[tuple[int, str], str],
) -> dict[int, dict[str, str]]:
    """Group (headword_id, column) edits into per-headword change dicts."""
    changes_by_id: dict[int, dict[str, str]] = {}
    for (headword_id, col_name), value in modified_cells.items():
        changes_by_id.setdefault(headword_id, {})[col_name] = value
    return changes_by_id


def effective_total(total: int, limit: int) -> int:
    """Total rows available to page through, capped by a positive limit."""
    if limit > 0:
        return min(total, limit)
    return total


def clamp_page_index(page_index: int, total: int, page_size: int) -> int:
    """Keep the page index within [0, last_page]."""
    if total <= 0 or page_size <= 0:
        return 0
    last_page = (total - 1) // page_size
    return max(0, min(page_index, last_page))


def page_label(page_index: int, page_size: int, total: int) -> str:
    """Human-readable range label, e.g. '101–200 of 5432'."""
    if total <= 0:
        return "0 of 0"
    start = page_index * page_size + 1
    end = min((page_index + 1) * page_size, total)
    return f"{start}–{end} of {total}"
