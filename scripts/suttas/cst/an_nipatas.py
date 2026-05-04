"""Extract AN nipāta rows from CST XML files into a TSV."""

import csv
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.printer import printer as pr

OUT_PATH = Path("scripts/suttas/cst/an_nipatas.tsv")

CST_ROMN_DIR = Path("resources/dpd_submodules/cst/romn")

AN_CST_FILES: list[tuple[str, Path]] = [
    ("AN1", CST_ROMN_DIR / "s0401m.mul.xml"),
    ("AN2", CST_ROMN_DIR / "s0402m1.mul.xml"),
    ("AN3", CST_ROMN_DIR / "s0402m2.mul.xml"),
    ("AN4", CST_ROMN_DIR / "s0402m3.mul.xml"),
    ("AN5", CST_ROMN_DIR / "s0403m1.mul.xml"),
    ("AN6", CST_ROMN_DIR / "s0403m2.mul.xml"),
    ("AN7", CST_ROMN_DIR / "s0403m3.mul.xml"),
    ("AN8", CST_ROMN_DIR / "s0404m1.mul.xml"),
    ("AN9", CST_ROMN_DIR / "s0404m2.mul.xml"),
    ("AN10", CST_ROMN_DIR / "s0404m3.mul.xml"),
    ("AN11", CST_ROMN_DIR / "s0404m4.mul.xml"),
]

PB_ED_TO_FIELD: dict[str, str] = {
    "M": "cst_m_page",
    "V": "cst_v_page",
    "P": "cst_p_page",
    "T": "cst_t_page",
}

FIELDNAMES = [
    "book",
    "book_code",
    "dpd_code",
    "cst_code",
    "cst_nikaya",
    "cst_book",
    "cst_section",
    "cst_vagga",
    "cst_sutta",
    "cst_paranum",
    "cst_m_page",
    "cst_v_page",
    "cst_p_page",
    "cst_t_page",
    "cst_file",
]


def extract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for book_code, file_path in AN_CST_FILES:
        with file_path.open(encoding="utf-16") as f:
            soup = BeautifulSoup(f.read(), "xml")

        nikaya = ""
        book = ""
        page_state: dict[str, str] = {field: "" for field in PB_ED_TO_FIELD.values()}
        first_id = ""

        for node in soup.find_all(["div", "head", "p"]):
            if not isinstance(node, Tag):
                continue
            if node.get("rend", "") == "nikaya":
                nikaya = node.get_text(strip=True)
            if node.get("rend", "") == "book":
                book = node.get_text(strip=True)
            if not first_id and node.get("id", ""):
                first_id = str(node["id"]).replace("_", ".")
            if node.name == "p":
                for pb in node.find_all("pb"):
                    if not isinstance(pb, Tag):
                        continue
                    ed = str(pb.get("ed") or "")
                    n = str(pb.get("n") or "").strip()
                    field = PB_ED_TO_FIELD.get(ed)
                    if field and n and not page_state[field]:
                        page_state[field] = n
            if book and all(page_state.values()):
                break

        rows.append(
            {
                "book": "Aṅguttara Nikāya",
                "book_code": "AN",
                "dpd_code": "",
                "cst_code": first_id,
                "cst_nikaya": nikaya,
                "cst_book": book,
                "cst_section": "",
                "cst_vagga": "",
                "cst_sutta": "",
                "cst_paranum": "",
                "cst_m_page": page_state["cst_m_page"],
                "cst_v_page": page_state["cst_v_page"],
                "cst_p_page": page_state["cst_p_page"],
                "cst_t_page": page_state["cst_t_page"],
                "cst_file": str(
                    file_path.relative_to(Path("resources/dpd_submodules/cst"))
                ),
            }
        )

    return rows


def save(rows: list[dict[str, str]]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pr.tic()
    pr.yellow_title("extract AN nipātas — CST")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
