"""Extract AN vagga headwords from the DPD database into a TSV."""

import csv
import re
from collections import OrderedDict
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sort_naturally import alpha_num_key

OUT_PATH = Path("scripts/suttas/dpd/an_vaggas.tsv")

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

AN_MEANING2_RE = re.compile(
    r"Chapter\s+(\d+)\s+of\s+(.+?),\s+Aṅguttara\s+Nikāya\s+(\d+)\.(\d+(?:-\d+)*)",
    re.UNICODE,
)
AN_PAREN_CODE_RE = re.compile(r"\((AN\d+(?:\.\d+)?(?:-(?:\d+\.)?\d+)?)\)")


def extract() -> list[dict[str, str]]:
    session = get_db_session(ProjectPaths().dpd_db_path)
    rows: list[dict[str, str]] = []
    grouped: OrderedDict[str, list[DpdHeadword]] = OrderedDict()
    try:
        headwords = session.query(DpdHeadword).order_by(DpdHeadword.id).all()
        for hw in headwords:
            meaning_2 = hw.meaning_2 or ""
            if "Aṅguttara Nikāya" not in meaning_2:
                continue
            if not (
                (hw.family_set or "").startswith("vaggas of Aṅguttara Nikāya")
                or meaning_2.startswith("Chapter ")
                or (hw.meaning_1 or "").startswith("Vagga ")
            ):
                continue
            match = AN_MEANING2_RE.search(meaning_2)
            if match is None:
                paren_match = AN_PAREN_CODE_RE.search(hw.meaning_1 or "")
                if paren_match is None:
                    paren_match = AN_PAREN_CODE_RE.search(meaning_2)
                if paren_match is None:
                    continue
                dpd_code = paren_match.group(1)
            else:
                dpd_code = f"AN{match.group(3)}.{match.group(4)}"
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
    pr.yellow_title("extract AN vaggas — DPD")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
