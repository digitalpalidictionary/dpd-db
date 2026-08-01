"""Convert the PTS↔CST concordance XLSX into a vendored, deterministically sorted TSV.

Source: https://github.com/jorgecaa/pts-vri-concordance (Jorge Contreras, CC0).

The build reads only the TSV; this script is run by hand when the upstream
concordance changes.
"""

import math
import re
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

from tools.paths import ProjectPaths
from tools.printer import printer as pr

XLSX_URL = "https://github.com/jorgecaa/pts-vri-concordance/raw/main/PTS-CST_Concordance_of_the_Pali_Canon.xlsx"

TSV_COLUMNS = [
    "cst_file",
    "cst_paranum",
    "pts_ref",
    "nikaya",
    "work",
    "number",
    "title",
]

# A sutta_info row that starts at paragraph N is best described by the entry whose
# locus IS paragraph N, so a plain paragraph outranks a range, which outranks a
# sub-item inside the paragraph.
FORM_RANK = {"n": 0, "a-b": 1, "n.item": 2}


def cell(value: object) -> str:
    """Render a cell as a TSV-safe string, blanking pandas NaN."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def download_xlsx() -> bytes | None:
    """Download the concordance XLSX, returning None on failure."""
    try:
        pr.green_tmr("downloading pts concordance")
        response = requests.get(XLSX_URL, timeout=(10, 60))
        response.raise_for_status()
        pr.yes("ok")
        return response.content
    except Exception as e:
        pr.no("failed")
        pr.red(str(e))
        return None


def classify_cst_ref(cst_ref: str) -> tuple[str, str, str] | None:
    """Split a CST reference into (file stem, form, start paragraph).

    Returns None for the chapter-relative forms (`file:cN`, `file:cN.item`,
    `file:cN.a-b`), whose numbering restarts inside each chapter and so cannot be
    resolved to a CST paragraph number without the chapter structure of the XML.
    """
    stem, _, rest = cst_ref.partition(":")
    if not stem or not rest:
        return None
    if re.fullmatch(r"\d+", rest):
        return stem, "n", rest
    if match := re.fullmatch(r"(\d+)-\d+", rest):
        return stem, "a-b", match.group(1)
    if match := re.fullmatch(r"(\d+)\.\d+", rest):
        return stem, "n.item", match.group(1)
    return None


def read_concordance(xlsx: bytes | Path) -> pd.DataFrame:
    """Read the Concordance sheet of the XLSX."""
    source = BytesIO(xlsx) if isinstance(xlsx, bytes) else xlsx
    pr.green_tmr("reading concordance sheet")
    df = pd.read_excel(source, sheet_name="Concordance")
    pr.yes(len(df))
    return df


def build_rows(df: pd.DataFrame) -> tuple[list[dict[str, str]], int, int]:
    """Convert collated entries into TSV rows keyed by (cst_file, cst_paranum).

    Returns the rows, the number of collated entries, and the number of
    chapter-relative entries skipped.
    """
    collated = df[df["Status"] == "Collated"]
    best: dict[tuple[str, int], tuple[int, int, dict[str, str]]] = {}
    skipped_chapter_form = 0

    for order, (_, entry) in enumerate(collated.iterrows()):
        parsed = classify_cst_ref(str(entry["CST reference"]))
        if parsed is None:
            skipped_chapter_form += 1
            continue
        stem, form, paranum = parsed
        key = (f"romn/{stem}.mul.xml", int(paranum))
        rank = (FORM_RANK[form], order)
        if key in best and best[key][:2] <= rank:
            continue
        best[key] = (
            *rank,
            {
                "cst_file": key[0],
                "cst_paranum": paranum,
                "pts_ref": cell(entry["PTS reference"]),
                "nikaya": cell(entry["Nikāya"]),
                "work": cell(entry["Work"]),
                "number": cell(entry["Number"]),
                "title": cell(entry["Title"]),
            },
        )

    rows = [best[key][2] for key in sorted(best)]
    return rows, len(collated), skipped_chapter_form


def write_tsv(rows: list[dict[str, str]], tsv_path: Path) -> None:
    """Write the rows to the vendored TSV."""
    pr.green_tmr("writing pts concordance tsv")
    lines = ["\t".join(TSV_COLUMNS)]
    lines.extend("\t".join(row[column] for column in TSV_COLUMNS) for row in rows)
    tsv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    pr.yes(len(rows))


def main() -> None:
    pr.tic()
    pr.yellow_title("convert pts concordance")
    pth = ProjectPaths()

    xlsx: bytes | Path
    if len(sys.argv) > 1:
        xlsx = Path(sys.argv[1])
        if not xlsx.exists():
            pr.red(f"no such file: {xlsx}")
            pr.toc()
            return
    else:
        downloaded = download_xlsx()
        if downloaded is None:
            pr.red("cannot convert without the source xlsx")
            pr.toc()
            return
        xlsx = downloaded

    df = read_concordance(xlsx)
    rows, collated_count, skipped_chapter_form = build_rows(df)

    pr.summary("entries read", len(df))
    pr.summary("collated", collated_count)
    pr.summary("chapter-form skipped", skipped_chapter_form)
    pr.summary("join keys written", len(rows))

    write_tsv(rows, pth.pts_concordance_tsv_path)
    pr.toc()


if __name__ == "__main__":
    main()
