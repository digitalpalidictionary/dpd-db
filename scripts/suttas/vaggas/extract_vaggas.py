"""Export AN vagga data into separate source TSVs for manual alignment.

Each TSV uses the same source column names that ultimately feed `sutta_info.tsv`,
but split by source:
- DPD
- CST
- SC
- BJT
"""

from __future__ import annotations

import csv
import json
import re
from collections import OrderedDict
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr

OUT_DIR = Path("scripts/suttas/vaggas")
DPD_OUT = OUT_DIR / "extract_vaggas_dpd.tsv"
CST_OUT = OUT_DIR / "extract_vaggas_cst.tsv"
SC_OUT = OUT_DIR / "extract_vaggas_sc.tsv"
BJT_OUT = OUT_DIR / "extract_vaggas_bjt.tsv"

CST_ROMN_DIR = Path("resources/dpd_submodules/cst/romn")
SC_PALI_DIR = Path("resources/sc-data/sc_bilara_data/root/pli/ms/sutta/an")
SC_ENG_DIR = Path("resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/an")
BJT_AN_TSV = Path("scripts/suttas/bjt/an.tsv")

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

PB_ED_TO_FIELD = {
    "M": "cst_m_page",
    "V": "cst_v_page",
    "P": "cst_p_page",
    "T": "cst_t_page",
}
NUM_AT_START_RE = re.compile(r"^\s*(\d+)\s*\.")
AN_MEANING2_RE = re.compile(
    r"Chapter\s+(\d+)\s+of\s+(.+?),\s+Aṅguttara\s+Nikāya\s+(\d+)\.(\d+(?:-\d+)*)",
    re.UNICODE,
)
AN_PAREN_CODE_RE = re.compile(r"\((AN\d+(?:\.\d+)?(?:-(?:\d+\.)?\d+)?)\)")


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def export_dpd() -> list[dict[str, str]]:
    fieldnames = [
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
    session = get_db_session(ProjectPaths().dpd_db_path)
    rows: list[dict[str, str]] = []
    grouped: OrderedDict[str, list[DpdHeadword]] = OrderedDict()
    try:
        headwords = session.query(DpdHeadword).order_by(DpdHeadword.id).all()
        for headword in headwords:
            meaning_2 = headword.meaning_2 or ""
            if "Aṅguttara Nikāya" not in meaning_2:
                continue
            if not (
                (headword.family_set or "").startswith("vaggas of Aṅguttara Nikāya")
                or meaning_2.startswith("Chapter ")
                or (headword.meaning_1 or "").startswith("Vagga ")
            ):
                continue
            match = AN_MEANING2_RE.search(meaning_2)
            if match is None:
                paren_match = AN_PAREN_CODE_RE.search(headword.meaning_1 or "")
                if paren_match is None:
                    paren_match = AN_PAREN_CODE_RE.search(meaning_2)
                if paren_match is None:
                    continue
                dpd_code = paren_match.group(1)
            else:
                dpd_code = f"AN{match.group(3)}.{match.group(4)}"
            grouped.setdefault(dpd_code, []).append(headword)

        for dpd_code, members in grouped.items():
            primary = members[0]
            variants = "; ".join(member.lemma_1 for member in members[1:])
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

    write_tsv(DPD_OUT, fieldnames, rows)
    return rows


def _update_pages(node: Tag, page_state: dict[str, str]) -> None:
    for pb in node.find_all("pb"):
        if not isinstance(pb, Tag):
            continue
        ed = str(pb.get("ed") or "")
        n = str(pb.get("n") or "").strip()
        field = PB_ED_TO_FIELD.get(ed)
        if field and n:
            page_state[field] = n


def _parse_body_num(text: str) -> str | None:
    match = NUM_AT_START_RE.match(text)
    return match.group(1) if match else None


def _format_range_code(book_code: str, first_num: str, last_num: str) -> str:
    if first_num == last_num:
        return f"{book_code}.{first_num}"
    return f"{book_code}.{first_num}-{last_num}"


def export_cst() -> list[dict[str, str]]:
    fieldnames = [
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
    rows: list[dict[str, str]] = []
    for book_code, file_path in AN_CST_FILES:
        with file_path.open(encoding="utf-16") as f:
            soup = BeautifulSoup(f.read(), "xml")

        nikaya = ""
        book = ""
        section = ""
        current_id = ""
        page_state = {field: "" for field in PB_ED_TO_FIELD.values()}
        active: dict[str, str] | None = None
        active_first_num = ""
        active_last_num = ""

        def flush_active() -> None:
            nonlocal active, active_first_num, active_last_num
            if active is None or not active_first_num:
                active = None
                active_first_num = ""
                active_last_num = ""
                return
            active["dpd_code"] = _format_range_code(
                book_code, active_first_num, active_last_num or active_first_num
            )
            rows.append(active)
            active = None
            active_first_num = ""
            active_last_num = ""

        for node in soup.find_all(["div", "head", "p"]):
            if not isinstance(node, Tag):
                continue
            if node.get("rend", "") == "nikaya":
                nikaya = node.get_text(strip=True)
            if node.get("rend", "") == "book":
                book = node.get_text(strip=True)
            if node.get("id", ""):
                current_id = str(node["id"]).replace("_", ".")
            if node.name == "p":
                _update_pages(node, page_state)
            if node.get("rend", "") == "title":
                section = node.get_text(strip=True)
            if node.get("rend", "") == "chapter":
                flush_active()
                active = {
                    "book": "Aṅguttara Nikāya",
                    "book_code": "AN",
                    "dpd_code": "",
                    "cst_code": current_id,
                    "cst_nikaya": nikaya,
                    "cst_book": book,
                    "cst_section": section,
                    "cst_vagga": re.sub(r"\(\d*\)\s", "", node.get_text(strip=True)),
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
                continue
            if active is None:
                continue
            if node.get("rend", "") == "subhead":
                sutta_num = _parse_body_num(node.get_text(strip=True))
                if not sutta_num:
                    continue
                active_last_num = sutta_num
                if not active_first_num:
                    active_first_num = sutta_num
                    active["cst_code"] = f"{current_id}.{sutta_num}"
                    active["cst_sutta"] = node.get_text(strip=True)
                    active["cst_paranum"] = sutta_num
                continue
            if node.name == "p" and node.get("rend", "") == "bodytext":
                body_num = _parse_body_num(node.get_text(strip=True))
                if not body_num:
                    continue
                active_last_num = body_num
                if not active_first_num:
                    active_first_num = body_num
                    active["cst_code"] = f"{current_id}.{body_num}"
                    active["cst_paranum"] = body_num

        flush_active()

    write_tsv(CST_OUT, fieldnames, rows)
    return rows


def _read_json(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return {str(key): str(value) for key, value in data.items()}


def export_sc() -> list[dict[str, str]]:
    fieldnames = [
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
    rows: list[dict[str, str]] = []

    grouped: OrderedDict[tuple[str, str], dict[str, str]] = OrderedDict()
    for pali_path in sorted(SC_PALI_DIR.rglob("*_root-pli-ms.json")):
        pali_data = _read_json(pali_path)
        english_path = SC_ENG_DIR / pali_path.relative_to(SC_PALI_DIR)
        english_path = Path(
            str(english_path).replace("root-pli-ms", "translation-en-sujato")
        )
        english_data = _read_json(english_path) if english_path.exists() else {}

        rel_path = str(pali_path.relative_to(Path("resources/sc-data")))
        folder = pali_path.parent.name
        keys = list(pali_data.keys())
        if not keys:
            continue
        base_code = keys[0].split(":")[0]
        upper_code = base_code.upper()

        if folder in {"an1", "an2"}:
            sc_code = pali_path.name.replace("_root-pli-ms.json", "").upper()
            row = {
                "book": "Aṅguttara Nikāya",
                "book_code": "AN",
                "dpd_code": sc_code,
                "sc_code": sc_code,
                "sc_book": (pali_data.get(f"{base_code}:0.1") or "").strip(),
                "sc_vagga": (pali_data.get(f"{base_code}:0.2") or "").strip(),
                "sc_sutta": "",
                "sc_eng_sutta": (english_data.get(f"{base_code}:0.2") or "").strip(),
                "sc_blurb": "",
                "sc_card_link": f"https://suttacentral.net/{sc_code.lower()}",
                "sc_pali_link": f"https://suttacentral.net/{sc_code.lower()}/pli/ms",
                "sc_eng_link": f"https://suttacentral.net/{sc_code.lower()}/en/sujato",
                "sc_file_path": rel_path,
            }
            rows.append(row)
            continue

        book = (pali_data.get(f"{base_code}:0.1") or "").strip()
        vagga = (pali_data.get(f"{base_code}:0.2") or "").strip()
        sutta = (pali_data.get(f"{base_code}:0.3") or "").strip()
        eng_sutta = (english_data.get(f"{base_code}:0.3") or "").strip()
        key = (book, vagga)
        if key not in grouped:
            grouped[key] = {
                "book": "Aṅguttara Nikāya",
                "book_code": "AN",
                "dpd_code": upper_code,
                "sc_code": upper_code,
                "sc_book": book,
                "sc_vagga": vagga,
                "sc_sutta": sutta,
                "sc_eng_sutta": eng_sutta,
                "sc_blurb": "",
                "sc_card_link": f"https://suttacentral.net/{upper_code.lower()}",
                "sc_pali_link": f"https://suttacentral.net/{upper_code.lower()}/pli/ms",
                "sc_eng_link": f"https://suttacentral.net/{upper_code.lower()}/en/sujato",
                "sc_file_path": rel_path,
            }

    rows.extend(grouped.values())
    write_tsv(SC_OUT, fieldnames, rows)
    return rows


def _bjt_group_sort_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("bjt_book", ""),
        row.get("bjt_minor_section", ""),
        row.get("bjt_vagga", ""),
    )


def export_bjt() -> list[dict[str, str]]:
    fieldnames = [
        "book",
        "book_code",
        "dpd_code",
        "bjt_sutta_code",
        "bjt_web_code",
        "bjt_filename",
        "bjt_book_id",
        "bjt_page_num",
        "bjt_page_offset",
        "bjt_piṭaka",
        "bjt_nikāya",
        "bjt_major_section",
        "bjt_book",
        "bjt_minor_section",
        "bjt_vagga",
        "bjt_sutta",
    ]
    rows: list[dict[str, str]] = []
    with BJT_AN_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        last_key: tuple[str, str, str] | None = None
        for row in reader:
            key = _bjt_group_sort_key(row)
            if key == last_key:
                continue
            last_key = key
            rows.append(
                {
                    "book": "Aṅguttara Nikāya",
                    "book_code": "AN",
                    "dpd_code": "",
                    "bjt_sutta_code": row.get("bjt_sutta_code", ""),
                    "bjt_web_code": row.get("bjt_web_code", ""),
                    "bjt_filename": row.get("bjt_filename", ""),
                    "bjt_book_id": row.get("bjt_book_id", ""),
                    "bjt_page_num": row.get("bjt_page_num", ""),
                    "bjt_page_offset": row.get("bjt_page_offset", ""),
                    "bjt_piṭaka": row.get("bjt_piṭaka", ""),
                    "bjt_nikāya": row.get("bjt_nikāya", ""),
                    "bjt_major_section": row.get("bjt_major_section", ""),
                    "bjt_book": row.get("bjt_book", ""),
                    "bjt_minor_section": row.get("bjt_minor_section", ""),
                    "bjt_vagga": row.get("bjt_vagga", ""),
                    "bjt_sutta": row.get("bjt_sutta", ""),
                }
            )
    write_tsv(BJT_OUT, fieldnames, rows)
    return rows


def main() -> None:
    pr.tic()
    pr.yellow_title("export AN vagga sources")

    pr.green_tmr("exporting dpd")
    dpd_rows = export_dpd()
    pr.yes(str(len(dpd_rows)))

    pr.green_tmr("exporting cst")
    cst_rows = export_cst()
    pr.yes(str(len(cst_rows)))

    pr.green_tmr("exporting sc")
    sc_rows = export_sc()
    pr.yes(str(len(sc_rows)))

    pr.green_tmr("exporting bjt")
    bjt_rows = export_bjt()
    pr.yes(str(len(bjt_rows)))

    pr.toc()


if __name__ == "__main__":
    main()
