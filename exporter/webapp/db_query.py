"""Database Query tab: find DpdHeadword rows by the contents of their columns.

Every filter becomes a regex on one column, matched with `regexp_match` as in
gui2's filter tab. In the webapp the route runs inside `regex_deadline`, so the
time and pattern limits of the other regex searches apply here too.
"""

import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import ColumnElement, String, and_, cast, inspect, or_
from sqlalchemy.orm import Session

from db.models import DpdHeadword

MAX_LIMIT = 100
# Each filter is one regex run on every row, and the shared compile cache in
# tools/search_deadline.py holds 16 patterns. Around 1000 filters SQLite also
# refuses the query as too deep.
MAX_FILTERS = 10
SEARCH_TYPES = ("contains", "starts_with", "ends_with", "regex")
LOGIC = ("and", "or")
COLUMNS: list[str] = [column.key for column in inspect(DpdHeadword).columns]
DEFAULT_COLUMNS = [
    "id",
    "pos",
    "grammar",
    "lemma_1",
    "meaning_1",
    "meaning_lit",
    "meaning_2",
    "construction",
]


class QueryError(ValueError):
    """A request the query cannot be built from. The message is safe to show."""


@dataclass(frozen=True)
class QueryFilter:
    column: str
    search_type: str
    value: str
    # How this filter joins the one before it. "or" starts a new group.
    logic: str = "and"


def make_filters(
    columns: list[str], search_types: list[str], values: list[str], logic: list[str]
) -> list[QueryFilter]:
    """Zip the request's parallel lists into filters and check each part."""
    if not len(columns) == len(search_types) == len(values) == len(logic):
        raise QueryError(
            "Each filter needs a field, a search type, a value and a logic."
        )
    if len(columns) > MAX_FILTERS:
        raise QueryError(f"Use at most {MAX_FILTERS} filters.")
    filters: list[QueryFilter] = []
    for column, search_type, value, joiner in zip(columns, search_types, values, logic):
        if column not in COLUMNS:
            raise QueryError(f"Unknown field: {column}")
        if search_type not in SEARCH_TYPES:
            raise QueryError(f"Unknown search type: {search_type}")
        if joiner not in LOGIC:
            raise QueryError(f"Unknown logic: {joiner}")
        filters.append(QueryFilter(column, search_type, value, joiner))
    return filters


def check_columns(columns: list[str]) -> list[str]:
    """The columns to return, in the order asked for, without repeats."""
    unknown = [column for column in columns if column not in COLUMNS]
    if unknown:
        raise QueryError(f"Unknown field: {unknown[0]}")
    return list(dict.fromkeys(columns)) or DEFAULT_COLUMNS


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))


def to_pattern(search_type: str, value: str) -> str:
    """The regex for a search type. Only "regex" passes the value through."""
    if search_type == "regex":
        return value
    escaped = re.escape(value)
    if search_type == "starts_with":
        return f"^{escaped}"
    if search_type == "ends_with":
        # $ also matches before a final line break, and freq_data ends in one
        return rf"{escaped}\Z"
    return escaped


def group_filters(filters: list[QueryFilter]) -> list[list[QueryFilter]]:
    """Split at each "or": a AND b OR c AND d is (a AND b) OR (c AND d).

    A filter with no value matches everything, so it is left out, and a group
    left empty is dropped.
    """
    groups: list[list[QueryFilter]] = [[]]
    for i, query_filter in enumerate(filters):
        if i > 0 and query_filter.logic == "or":
            groups.append([])
        if query_filter.value != "":
            groups[-1].append(query_filter)
    return [group for group in groups if group]


def filter_condition(query_filter: QueryFilter) -> ColumnElement[bool]:
    column = getattr(DpdHeadword, query_filter.column)
    # REGEXP gets the column's own value, so numbers and dates are matched as text
    if not isinstance(column.type, String):
        column = cast(column, String)
    return column.regexp_match(to_pattern(query_filter.search_type, query_filter.value))


def build_condition(filters: list[QueryFilter]) -> ColumnElement[bool] | None:
    """The WHERE clause for the filters, or None when there is nothing to match."""
    groups = [
        and_(*[filter_condition(query_filter) for query_filter in group])
        for group in group_filters(filters)
    ]
    if not groups:
        return None
    return or_(*groups)


def cell_value(value: object) -> str | int:
    if value is None:
        return ""
    if isinstance(value, int):
        return value
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    return str(value)


def run_query(
    db_session: Session, filters: list[QueryFilter], columns: list[str], limit: int
) -> tuple[list[list[str | int]], bool]:
    """Up to `limit` rows of the columns, by id, and whether there are more."""
    query = db_session.query(*[getattr(DpdHeadword, column) for column in columns])
    condition = build_condition(filters)
    if condition is not None:
        query = query.filter(condition)
    # one row past the limit tells us there are more
    results = query.order_by(DpdHeadword.id).limit(limit + 1).all()
    rows = [[cell_value(value) for value in result] for result in results[:limit]]
    return rows, len(results) > limit
