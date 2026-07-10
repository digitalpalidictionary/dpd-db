"""3.5: DB tab (filter_component.py) query + table-build wall-clock at
various limits, with query time and Python/Flet-control-construction time
measured separately to see which dominates. Reimplements the exact
query-then-build algorithm from gui2/filter_component.py (_apply_filters +
_update_results_table) as free functions, since FilterComponent itself
needs a live flet.Page to construct (calls self.update()/page.update()).
"""

import time

import flet as ft

from bench_common import force_throwaway_db_globally, write_result
from db.models import DpdHeadword
from gui2.database_manager import DatabaseManager

# Must run before any DatabaseManager method is CALLED (not before import —
# Python resolves module-global names lazily at call time via __globals__,
# so patching after import but before use is sufficient).
force_throwaway_db_globally()

DISPLAY_COLUMNS = [
    "id",
    "lemma_1",
    "meaning_1",
    "meaning_lit",
    "root_key",
    "family_root",
]


def run_query(db_manager: DatabaseManager, limit: int) -> tuple[list, float]:
    start = time.perf_counter()
    query = db_manager.db_session.query(DpdHeadword).order_by(DpdHeadword.lemma_1)
    if limit > 0:
        query = query.limit(limit)
    results = query.all()
    elapsed_ms = (time.perf_counter() - start) * 1000
    return results, elapsed_ms


def build_table(results: list, display_columns: list[str]) -> float:
    """Mirrors gui2/filter_component.py's _update_results_table: column-width
    scan (iterates every cell once) then builds one ft.DataRow with one
    CellTextField per cell, exactly as the real DB tab does."""
    start = time.perf_counter()

    column_widths = {}
    for col_name in display_columns:
        max_len = len(col_name)
        for result in results:
            value = getattr(result, col_name, "")
            value_str = "" if value is None else str(value)
            max_len = max(max_len, len(value_str))
        column_widths[col_name] = max(120, min(max_len * 8, 500))

    columns = [ft.DataColumn(label=ft.Text("#"))]
    for col_name in display_columns:
        columns.append(ft.DataColumn(label=ft.Text(col_name)))

    rows = []
    for row_index, result in enumerate(results):
        cells = [ft.DataCell(ft.TextField(value=str(row_index + 1), read_only=True))]
        for col_name in display_columns:
            value = getattr(result, col_name, "")
            value_str = "" if value is None else str(value)
            text_field = ft.TextField(value=value_str, multiline=True)
            cells.append(ft.DataCell(text_field))
        rows.append(ft.DataRow(cells=cells))

    elapsed_ms = (time.perf_counter() - start) * 1000
    return elapsed_ms


def run_paged_query(
    db_manager: DatabaseManager, limit: int, page_index: int
) -> tuple[list, float, int]:
    """Mirrors the Phase 5 FilterComponent._apply_filters: count() for the
    pagination label, then fetch one PAGE_SIZE page via offset/limit."""
    from gui2.filter_component import PAGE_SIZE
    from gui2.filter_logic import clamp_page_index, effective_total

    start = time.perf_counter()
    query = db_manager.db_session.query(DpdHeadword).order_by(
        DpdHeadword.lemma_1, DpdHeadword.id
    )
    total = effective_total(query.count(), limit)
    page_index = clamp_page_index(page_index, total, PAGE_SIZE)
    page_offset = page_index * PAGE_SIZE
    page_limit = min(PAGE_SIZE, total - page_offset)
    results = query.offset(page_offset).limit(page_limit).all() if page_limit else []
    elapsed_ms = (time.perf_counter() - start) * 1000
    return results, elapsed_ms, total


def build_table_readonly(results: list, display_columns: list[str]) -> float:
    """Mirrors the Phase 5 FilterComponent._update_results_table: width scan
    via filter_logic, then read-only ft.Text cells with build-time spell
    check on meaning columns (the real per-page render cost)."""
    import re as re_mod

    from gui2.filter_logic import cell_value_str, compute_column_widths
    from tools.spelling import CustomSpellChecker

    spellchecker = CustomSpellChecker()

    start = time.perf_counter()
    column_widths = compute_column_widths(results, display_columns)

    columns = [ft.DataColumn(label=ft.Text("#"))]
    for col_name in display_columns:
        columns.append(ft.DataColumn(label=ft.Text(col_name)))

    rows = []
    for row_index, result in enumerate(results):
        cells = [ft.DataCell(ft.Text(value=str(row_index + 1), size=12))]
        for col_name in display_columns:
            value_str = cell_value_str(getattr(result, col_name, ""))
            width = column_widths.get(col_name, 150)
            misspelled = bool(
                col_name in ("meaning_1", "meaning_lit", "meaning_2")
                and value_str
                and spellchecker.has_misspellings(re_mod.sub(r"<[^>]+>", "", value_str))
            )
            color = ft.Colors.RED if misspelled else ft.Colors.GREY_300
            cells.append(
                ft.DataCell(ft.Text(value=value_str, width=width, size=12, color=color))
            )
        rows.append(ft.DataRow(cells=cells))

    elapsed_ms = (time.perf_counter() - start) * 1000
    return elapsed_ms


def main() -> None:
    db_manager = DatabaseManager()
    limits = [100, 1000, 10000, 0]  # 0 = all ~83k rows, matching DEFAULT_LIMIT

    results_by_limit = {}
    for limit in limits:
        results, query_ms = run_query(db_manager, limit)
        build_ms = build_table(results, DISPLAY_COLUMNS)
        row_count = len(results)
        results_by_limit[str(limit) if limit else "0 (all)"] = {
            "row_count": row_count,
            "query_ms": round(query_ms, 2),
            "build_ms": round(build_ms, 2),
            "total_ms": round(query_ms + build_ms, 2),
        }
        print(
            f"limit={limit or 'ALL':>6}  rows={row_count:>6}  "
            f"query={query_ms:>9.2f}ms  build={build_ms:>9.2f}ms  "
            f"total={query_ms + build_ms:>9.2f}ms"
        )

    write_result("3.5_db_tab", results_by_limit)

    # Phase 5 "after" numbers: same user limits, but every apply now fetches
    # and renders ONE page. Also probe a deep page (offset ~40k) at limit 0.
    print("\nPhase 5 paged pipeline (PAGE_SIZE=100 per apply):")
    after: dict[str, dict] = {}
    scenarios = [(limit, 0) for limit in limits] + [(0, 400)]
    for limit, page_index in scenarios:
        results, query_ms, total = run_paged_query(db_manager, limit, page_index)
        build_ms = build_table_readonly(results, DISPLAY_COLUMNS)
        key = f"limit={limit or '0 (all)'} page={page_index}"
        after[key] = {
            "rows_rendered": len(results),
            "total_matched": total,
            "query_ms": round(query_ms, 2),
            "build_ms": round(build_ms, 2),
            "total_ms": round(query_ms + build_ms, 2),
        }
        print(
            f"limit={limit or 'ALL':>6}  page={page_index:>3}  "
            f"rows={len(results):>4}  query={query_ms:>8.2f}ms  "
            f"build={build_ms:>8.2f}ms  total={query_ms + build_ms:>8.2f}ms"
        )

    write_result("5.6_db_tab_after", after)


if __name__ == "__main__":
    main()
