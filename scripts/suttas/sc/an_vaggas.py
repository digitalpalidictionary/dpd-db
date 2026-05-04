"""Extract AN vagga rows from SC JSON files into a TSV.

One row per (book, vagga) group — each vagga is represented once with the
first sutta in that vagga as the representative sutta.
"""

import csv
import json
import re
from collections import OrderedDict
from pathlib import Path

from tools.printer import printer as pr
from tools.sort_naturally import alpha_num_key

PANNASAKA_RE = re.compile(r"paṇṇāsaka", re.IGNORECASE)

OUT_PATH = Path("scripts/suttas/sc/an_vaggas.tsv")

SC_PALI_DIR = Path("resources/sc-data/sc_bilara_data/root/pli/ms/sutta/an")
SC_ENG_DIR = Path("resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/an")

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


def _read_json(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return {str(k): str(v) for k, v in data.items()}


def extract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    grouped: OrderedDict[tuple[str, ...], dict[str, str]] = OrderedDict()

    for pali_path in sorted(SC_PALI_DIR.rglob("*_root-pli-ms.json")):
        pali_data = _read_json(pali_path)
        eng_path = SC_ENG_DIR / pali_path.relative_to(SC_PALI_DIR)
        eng_path = Path(str(eng_path).replace("root-pli-ms", "translation-en-sujato"))
        eng_data = _read_json(eng_path) if eng_path.exists() else {}

        rel_path = str(pali_path.relative_to(Path("resources/sc-data")))
        folder = pali_path.parent.name
        keys = list(pali_data.keys())
        if not keys:
            continue
        base_code = keys[0].split(":")[0]
        upper_code = base_code.upper()

        # an1 and an2 have a different structure — one row per file
        if folder in {"an1", "an2"}:
            sc_code = pali_path.name.replace("_root-pli-ms.json", "").upper()
            rows.append(
                {
                    "book": "Aṅguttara Nikāya",
                    "book_code": "AN",
                    "dpd_code": "",
                    "sc_code": sc_code,
                    "sc_book": (pali_data.get(f"{base_code}:0.1") or "").strip(),
                    "sc_vagga": (pali_data.get(f"{base_code}:0.2") or "").strip(),
                    "sc_sutta": "",
                    "sc_eng_sutta": (eng_data.get(f"{base_code}:0.2") or "").strip(),
                    "sc_blurb": "",
                    "sc_card_link": f"https://suttacentral.net/{sc_code.lower()}",
                    "sc_pali_link": f"https://suttacentral.net/{sc_code.lower()}/pli/ms",
                    "sc_eng_link": f"https://suttacentral.net/{sc_code.lower()}/en/sujato",
                    "sc_file_path": rel_path,
                }
            )
            continue

        nipata_num = re.sub(r"\D", "", folder)
        sc_book = f"Aṅguttara Nikāya {nipata_num}"
        field_02 = (pali_data.get(f"{base_code}:0.2") or "").strip()
        field_03 = (pali_data.get(f"{base_code}:0.3") or "").strip()

        # Some peyyāla sections (e.g. AN11) label :0.2 as the paṇṇāsaka and
        # put the actual vagga name at :0.3 — detect and promote accordingly.
        if PANNASAKA_RE.search(field_02):
            vagga = field_03
            sutta = ""
            eng_vagga = (eng_data.get(f"{base_code}:0.3") or "").strip()
            key: tuple[str, ...] = (folder, field_02, field_03)
        else:
            vagga = field_02
            sutta = field_03
            eng_vagga = (eng_data.get(f"{base_code}:0.2") or "").strip()
            key = (folder, field_02)

        if key not in grouped:
            grouped[key] = {
                "book": "Aṅguttara Nikāya",
                "book_code": "AN",
                "dpd_code": "",
                "sc_code": upper_code,
                "sc_book": sc_book,
                "sc_vagga": vagga,
                "sc_sutta": sutta,
                "sc_eng_sutta": eng_vagga,
                "sc_blurb": "",
                "sc_card_link": f"https://suttacentral.net/{upper_code.lower()}",
                "sc_pali_link": f"https://suttacentral.net/{upper_code.lower()}/pli/ms",
                "sc_eng_link": f"https://suttacentral.net/{upper_code.lower()}/en/sujato",
                "sc_file_path": rel_path,
            }

    rows.extend(grouped.values())
    rows.sort(key=lambda r: alpha_num_key(r["sc_code"]))
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
    pr.yellow_title("extract AN vaggas — SC")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
