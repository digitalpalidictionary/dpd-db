"""Extract AN nipāta headwords from the DPD database into a TSV."""

import csv
import re
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sort_naturally import alpha_num_key

OUT_PATH = Path("scripts/suttas/dpd/an_nipatas.tsv")

FIELDNAMES = [
    "book",
    "book_code",
    "dpd_code",
    "dpd_sutta",
    "dpd_sutta_var",
    "id",
    "lemma_1",
    "family_set",
    "meaning_1",
    "meaning_lit",
    "meaning_2",
    "notes",
]

AN_BOOK_NUM_RE = re.compile(r"Book (\d+) of the Aṅguttara Nikāya")


def extract() -> list[dict[str, str]]:
    session = get_db_session(ProjectPaths().dpd_db_path)
    rows: list[dict[str, str]] = []
    grouped: dict[str, list[DpdHeadword]] = {}
    try:
        headwords = session.query(DpdHeadword).order_by(DpdHeadword.id).all()
        for hw in headwords:
            if (hw.family_set or "") != "books of the Aṅguttara Nikāya":
                continue
            text = (hw.meaning_1 or "") or (hw.meaning_2 or "")
            match = AN_BOOK_NUM_RE.search(text)
            if match is None:
                continue
            dpd_code = f"AN{match.group(1)}"
            grouped.setdefault(dpd_code, []).append(hw)

        for dpd_code, members in grouped.items():
            primary = members[0]
            variants = "; ".join(m.lemma_1 for m in members[1:])
            rows.append(
                {
                    "book": "Aṅguttara Nikāya",
                    "book_code": "AN",
                    "dpd_code": dpd_code,
                    "dpd_sutta": primary.lemma_1,
                    "dpd_sutta_var": variants,
                    "id": str(primary.id),
                    "lemma_1": primary.lemma_1,
                    "family_set": primary.family_set or "",
                    "meaning_1": primary.meaning_1 or "",
                    "meaning_lit": primary.meaning_lit or "",
                    "meaning_2": primary.meaning_2 or "",
                    "notes": primary.notes or "",
                }
            )
    finally:
        session.close()
    rows.sort(key=lambda r: alpha_num_key(r["dpd_code"]))
    return rows


def save(rows: list[dict[str, str]]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pr.tic()
    pr.yellow_title("extract AN nipātas — DPD")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
