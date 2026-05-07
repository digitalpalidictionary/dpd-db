"""Extract AN vagga rows from CST XML files into a TSV."""

import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.printer import printer as pr
from tools.sort_naturally import alpha_num_key

OUT_PATH = Path("scripts/suttas/cst/an_vaggas.tsv")

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

NUM_AT_START_RE = re.compile(r"^\s*(\d+)(?:-(\d+))?\s*\.")
SUBVAGGA_RE = re.compile(r"vaggo\s*$", re.IGNORECASE)

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


def _update_pages(node: Tag, page_state: dict[str, str]) -> None:
    for pb in node.find_all("pb"):
        if not isinstance(pb, Tag):
            continue
        ed = str(pb.get("ed") or "")
        n = str(pb.get("n") or "").strip()
        field = PB_ED_TO_FIELD.get(ed)
        if field and n:
            page_state[field] = n


def _parse_body_nums(text: str) -> tuple[str, str] | None:
    """Return (first, last) from '157-163.' or ('11', '11') from '11.'"""
    match = NUM_AT_START_RE.match(text)
    if not match:
        return None
    first = match.group(1)
    last = match.group(2) or first
    return first, last


def _format_range_code(book_code: str, first_num: str, last_num: str) -> str:
    if first_num == last_num:
        return f"{book_code}.{first_num}"
    return f"{book_code}.{first_num}-{last_num}"


def extract() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for book_code, file_path in AN_CST_FILES:
        with file_path.open(encoding="utf-16") as f:
            soup = BeautifulSoup(f.read(), "xml")

        nikaya = ""
        book = ""
        section = ""
        current_id = ""
        page_state: dict[str, str] = {field: "" for field in PB_ED_TO_FIELD.values()}
        active: dict[str, str] | None = None
        active_first_num = ""
        active_last_num = ""
        chapter_ctx: dict[str, str] | None = None

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
                chapter_ctx = {
                    "book": "Aṅguttara Nikāya",
                    "book_code": "AN",
                    "cst_code": current_id,
                    "cst_nikaya": nikaya,
                    "cst_book": book,
                    "cst_section": section,
                    "cst_vagga": re.sub(r"\(\d*\)\s", "", node.get_text(strip=True)),
                    "cst_file": str(
                        file_path.relative_to(Path("resources/dpd_submodules/cst"))
                    ),
                }
                active = {
                    **chapter_ctx,
                    "dpd_code": "",
                    "cst_sutta": "",
                    "cst_paranum": "",
                    "cst_m_page": page_state["cst_m_page"],
                    "cst_v_page": page_state["cst_v_page"],
                    "cst_p_page": page_state["cst_p_page"],
                    "cst_t_page": page_state["cst_t_page"],
                }
                continue
            if active is None:
                continue
            if node.get("rend", "") == "subhead":
                subhead_text = node.get_text(strip=True)
                if SUBVAGGA_RE.search(subhead_text) and chapter_ctx is not None:
                    # Sub-vagga heading inside a chapter container (AN1 ch14-16)
                    ctx: dict[str, str] = chapter_ctx
                    # Promote the outer chapter name into cst_section the first time
                    # we encounter a sub-vagga (only when no higher section exists yet)
                    if not ctx["cst_section"]:
                        ctx["cst_section"] = ctx["cst_vagga"]
                    flush_active()
                    active = {
                        **ctx,
                        "dpd_code": "",
                        "cst_vagga": subhead_text,
                        "cst_sutta": "",
                        "cst_paranum": "",
                        "cst_m_page": page_state["cst_m_page"],
                        "cst_v_page": page_state["cst_v_page"],
                        "cst_p_page": page_state["cst_p_page"],
                        "cst_t_page": page_state["cst_t_page"],
                    }
                else:
                    # Subheads use local (per-vagga) numbering — only capture the sutta name
                    if not active["cst_sutta"]:
                        active["cst_sutta"] = subhead_text
                continue
            if node.name == "p" and node.get("rend", "") == "bodytext":
                # Bodytext carries global (continuous) sutta numbers — use these for the range
                nums = _parse_body_nums(node.get_text(strip=True))
                if not nums:
                    continue
                body_first, body_last = nums
                active_last_num = body_last
                if not active_first_num:
                    active_first_num = body_first
                    active["cst_code"] = f"{current_id}.{body_first}"
                    active["cst_paranum"] = body_first
                    active["cst_m_page"] = page_state["cst_m_page"]
                    active["cst_v_page"] = page_state["cst_v_page"]
                    active["cst_p_page"] = page_state["cst_p_page"]
                    active["cst_t_page"] = page_state["cst_t_page"]

        flush_active()

    rows.sort(key=lambda r: alpha_num_key(r["cst_code"]))
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
    pr.yellow_title("extract AN vaggas — CST")
    pr.green_tmr("extracting")
    rows = extract()
    pr.yes(str(len(rows)))
    pr.green_tmr(f"saving {OUT_PATH}")
    save(rows)
    pr.yes("done")
    pr.toc()


if __name__ == "__main__":
    main()
