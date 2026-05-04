"""Extract AN nipāta rows from SC JSON files into a TSV.

One row per nipāta (an1–an11). Columns match an_vaggas.tsv for direct paste.
"""

import csv
import re
from pathlib import Path

from tools.printer import printer as pr

OUT_PATH = Path("scripts/suttas/sc/an_nipatas.tsv")

SC_PALI_DIR = Path("resources/sc-data/sc_bilara_data/root/pli/ms/sutta/an")

FIELDNAMES = [
    "book",
    "book_code",
    "dpd_code",
    "sc_code",
    "sc_book",
    "sc_vagga",
    "sc_sutta",
    "sc_eng_sutta",
    "sc_blurb",
    "sc_card_link",
    "sc_pali_link",
    "sc_eng_link",
    "sc_file_path",
]

AN_FOLDERS = [f"an{n}" for n in range(1, 12)]


def extract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for folder in AN_FOLDERS:
        nipata_num = re.sub(r"\D", "", folder)
        folder_path = SC_PALI_DIR / folder
        pali_files = sorted(folder_path.rglob("*_root-pli-ms.json"))
        if not pali_files:
            continue

        rel_path = str(pali_files[0].relative_to(Path("resources/sc-data")))

        rows.append(
            {
                "book": "Aṅguttara Nikāya",
                "book_code": "AN",
                "dpd_code": "",
                "sc_code": folder.upper(),
                "sc_book": f"Aṅguttara Nikāya {nipata_num}",
                "sc_vagga": "",
                "sc_sutta": "",
                "sc_eng_sutta": f"Numbered Discourses {nipata_num}",
                "sc_blurb": "",
                "sc_card_link": f"https://suttacentral.net/{folder}",
                "sc_pali_link": f"https://suttacentral.net/{folder}/pli/ms",
                "sc_eng_link": f"https://suttacentral.net/{folder}/en/sujato",
                "sc_file_path": rel_path,
            }
        )

    return rows


def save(rows: list[dict[str, str]]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def main() -> None:
    pr.tic()
    pr.yellow_title("extract AN nipātas — SC")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
