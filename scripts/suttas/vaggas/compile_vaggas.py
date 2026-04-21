"""One-shot generator: produce vagga rows for sutta_info.tsv.

Output: scripts/suttas/vaggas/compile_vaggas.tsv
Same column layout as sutta_info.tsv plus a trailing `status` column.
Rows that resolved successfully have status="ok"; unresolved rows have a
failure reason and empty sutta-metadata columns so nothing gets silently lost.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

from icecream import ic

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.add.vagga_codes.shared import ANY_CODE_RE, DPD_CODE_RE
from tools.paths import ProjectPaths
from tools.printer import printer as pr

SUTTA_INFO_TSV = Path("db/backup_tsv/sutta_info.tsv")
OUTPUT_TSV = Path(__file__).parent / "compile_vaggas.tsv"


def first_sutta_from_range(dpd_code: str) -> str | None:
    """Extract the first sutta code from a range like MN1-10 or SN12.1-10."""
    m = DPD_CODE_RE.match(dpd_code)
    if not m:
        return None
    book, first_num, second_num = m.groups()
    if second_num:
        return f"{book}{first_num}.{second_num}"
    return f"{book}{first_num}"


def load_sutta_info() -> tuple[
    list[str],
    dict[str, dict[str, str]],
    list[str],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
]:
    """Return (headers, exact_map, ordered_codes, start_map, last_in_section_map).

    - exact_map: dpd_code → row
    - start_map: first-sutta-of-range → row  (resolves range-boundary mismatches)
    - last_in_section_map: '{book_code}{inner}' → last row in that section
      (SN samyutta fallback; inner = number before dot, e.g. 'SN49')
    """
    headers: list[str] = []
    exact_map: dict[str, dict[str, str]] = {}
    ordered_codes: list[str] = []
    start_map: dict[str, dict[str, str]] = {}
    last_in_section_map: dict[str, dict[str, str]] = {}

    with SUTTA_INFO_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = [h for h in (reader.fieldnames or []) if h]
        for row in reader:
            code = (row.get("dpd_code") or "").strip()
            if not code:
                continue
            row_dict = dict(row)
            exact_map[code] = row_dict
            ordered_codes.append(code)

            # start_map: first sutta of this code's range → row
            start = first_sutta_from_range(code)
            if start and start not in start_map:
                start_map[start] = row_dict

            # last_in_section_map: keep overwriting so last wins
            m = DPD_CODE_RE.match(code)
            if m:
                bk, outer, inner = m.groups()
                section_key = f"{bk}{outer}" if inner else f"{bk}"
                last_in_section_map[section_key] = row_dict

    return headers, exact_map, ordered_codes, start_map, last_in_section_map


def load_vagga_headwords(db_session) -> list[tuple[int, str, str]]:
    """Return list of (id, lemma_1, dpd_code) for vagga headwords."""
    results: list[tuple[int, str, str]] = []

    headwords = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.lemma_1.regexp_match(r"vagga\b"))
        .all()
    )

    for hw in headwords:
        if not hw.meaning_1:
            continue
        m = ANY_CODE_RE.search(hw.meaning_1)
        if not m:
            continue
        dpd_code = m.group(1)
        results.append((hw.id, hw.lemma_1, dpd_code))

    return results


def group_by_code(
    entries: list[tuple[int, str, str]],
) -> dict[str, tuple[str, str]]:
    """Group entries by dpd_code; return code -> (primary_lemma, var_lemmas).

    lemma_1 is kept verbatim (including homonym numbers) for DB lookup correctness.
    """
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for hw_id, lemma_1, dpd_code in entries:
        grouped[dpd_code].append((hw_id, lemma_1))

    result: dict[str, tuple[str, str]] = {}
    for dpd_code, members in grouped.items():
        members.sort(key=lambda x: x[0])
        primary = members[0][1]
        variants = "; ".join(lm for _, lm in members[1:])
        result[dpd_code] = (primary, variants)

    return result


def resolve_source_row(
    dpd_code: str,
    first_sutta: str,
    exact_map: dict[str, dict[str, str]],
    start_map: dict[str, dict[str, str]],
    last_in_section_map: dict[str, dict[str, str]],
) -> tuple[dict[str, str] | None, str]:
    """Try to find an anchor row; return (row_or_None, status).

    Resolution order:
    1. Exact match on first_sutta (e.g. SN12.1).
    2. Exact match on the full dpd_code (range-grouped suttas like SN46.77-88).
    3. SN: prefix match — sutta_info range starts at the same code (e.g. SN23.23-33
       resolves SN23.23).
    4. SN: last-row-of-samyutta fallback for genuine coverage gaps.
    5. Miss.
    """
    row = exact_map.get(first_sutta)
    if row is not None:
        return row, "ok"

    row = exact_map.get(dpd_code)
    if row is not None:
        return row, "ok"

    m = DPD_CODE_RE.match(first_sutta)
    book = m.group(1) if m else ""

    if book == "SN":
        # Prefix match: sutta_info may store the range with a slightly different end
        row = start_map.get(first_sutta)
        if row is not None:
            return row, "ok:sn_range_prefix"

        # Last-row fallback: find last row for this samyutta
        outer = m.group(2) if m else ""
        section_key = f"SN{outer}"
        row = last_in_section_map.get(section_key)
        if row is not None:
            return row, f"ok:sn_last_row({section_key})"

    if book == "AN" and first_sutta.startswith("AN1."):
        reason = "miss:an1_not_in_sutta_info"
    elif book == "DHP":
        reason = "miss:dhp_verse_vs_chapter"
    else:
        reason = f"miss:{first_sutta}_not_found"

    return None, reason


def main() -> None:
    pr.tic()
    pr.yellow_title("Vagga sutta_info row generator")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    pr.green_tmr("Loading sutta_info.tsv")
    headers, exact_map, ordered_codes, start_map, last_in_section_map = (
        load_sutta_info()
    )
    assert len(headers) == 44, f"Expected 44 columns, got {len(headers)}"
    ic(len(exact_map))
    pr.yes(str(len(exact_map)))

    pr.green_tmr("Loading vagga headwords from DB")
    vagga_entries = load_vagga_headwords(db_session)
    ic(len(vagga_entries))
    ic(vagga_entries[:5])
    pr.yes(str(len(vagga_entries)))

    pr.green_tmr("Grouping by dpd_code")
    grouped = group_by_code(vagga_entries)
    ic(len(grouped))
    pr.yes(str(len(grouped)))

    code_position: dict[str, int] = {c: i for i, c in enumerate(ordered_codes)}
    output_headers = headers + ["status"]

    pr.green_tmr("Building output rows")
    ok_rows: list[dict[str, str]] = []
    miss_rows: list[dict[str, str]] = []

    for dpd_code, (primary, variants) in grouped.items():
        first_sutta = first_sutta_from_range(dpd_code)
        if not first_sutta:
            print(f"SKIP unparseable: {dpd_code!r}", file=sys.stderr)
            continue

        source_row, status = resolve_source_row(
            dpd_code, first_sutta, exact_map, start_map, last_in_section_map
        )

        if source_row is not None:
            out_row = dict(source_row)
            out_row["dpd_code"] = dpd_code
            out_row["dpd_sutta"] = primary
            out_row["dpd_sutta_var"] = variants
            out_row["status"] = status
            out_row["_anchor"] = source_row["dpd_code"]
            ok_rows.append(out_row)
        else:
            miss_row: dict[str, str] = {k: "" for k in output_headers}
            miss_row["dpd_code"] = dpd_code
            miss_row["dpd_sutta"] = primary
            miss_row["dpd_sutta_var"] = variants
            miss_row["status"] = status
            miss_rows.append(miss_row)

    ic(len(ok_rows), len(miss_rows))
    pr.yes(f"{len(ok_rows)}ok/{len(miss_rows)}miss")

    pr.green_tmr("Sorting output rows")
    ok_rows.sort(key=lambda r: code_position.get(r.pop("_anchor"), 999999))
    miss_rows.sort(key=lambda r: r["dpd_code"])

    all_rows = ok_rows + miss_rows

    pr.green_tmr(f"Writing {OUTPUT_TSV}")
    OUTPUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_TSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_headers, delimiter="\t")
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: row.get(k, "") for k in output_headers})
    pr.yes("done")

    pr.toc()


if __name__ == "__main__":
    main()
