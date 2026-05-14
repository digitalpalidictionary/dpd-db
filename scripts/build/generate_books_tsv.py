"""One-shot generator for tools/cst_book_translator.tsv.

Merges three existing sources into a single canonical TSV keyed by
CST filename stem:

1. ``tools.pali_text_files.cst_texts``         gui_code -> [cst .txt files]
2. ``gui2.dpd_fields_examples.book_codes``     display name -> gui_code
3. ``db.bold_definitions.functions.file_list`` cst .xml filename -> DPD code

Output: tools/cst_book_translator.tsv
Columns: cst_filename, cst_book_name, gui_book_code, dpd_book_code

Run once; thereafter the TSV is hand-edited.
"""

import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

from db.bold_definitions.functions import file_list
from gui2.dpd_fields_examples import book_codes
from tools.paths import ProjectPaths
from tools.pali_text_files import cst_texts

# Map DPD book code -> nikāya / piṭaka prefix used in cst_book_name.
# Derived by grouping DPD codes from shared_data/help/abbreviations.tsv.
# Hand-curated; polish in the resulting TSV.
NIKAYA_PREFIX: dict[str, str] = {
    # vinaya
    "VIN": "Vinayapiṭaka",
    "VINa": "Vinayapiṭaka",
    "VINt": "Vinayapiṭaka",
    "KVA": "Vinayapiṭaka",
    "KVa": "Vinayapiṭaka",
    "KVt": "Vinayapiṭaka",
    "VSa": "Vinayapiṭaka",
    "VBt": "Vinayapiṭaka",
    "VMVt": "Vinayapiṭaka",
    "VAt": "Vinayapiṭaka",
    "VVUt": "Vinayapiṭaka",
    "VVt": "Vinayapiṭaka",
    "PYt": "Vinayapiṭaka",
    # dn / mn / sn / an
    "DN": "Dīghanikāya",
    "DNa": "Dīghanikāya",
    "DNt": "Dīghanikāya",
    "DNnt": "Dīghanikāya",
    "MN": "Majjhimanikāya",
    "MNa": "Majjhimanikāya",
    "MNt": "Majjhimanikāya",
    "SN": "Saṃyuttanikāya",
    "SNa": "Saṃyuttanikāya",
    "SNt": "Saṃyuttanikāya",
    "AN": "Aṅguttaranikāya",
    "ANa": "Aṅguttaranikāya",
    "ANt": "Aṅguttaranikāya",
    # khuddaka nikāya
    "KP": "Khuddakanikāya",
    "KPa": "Khuddakanikāya",
    "DHP": "Khuddakanikāya",
    "DHPa": "Khuddakanikāya",
    "UD": "Khuddakanikāya",
    "UDa": "Khuddakanikāya",
    "ITI": "Khuddakanikāya",
    "ITIa": "Khuddakanikāya",
    "SNP": "Khuddakanikāya",
    "SNPa": "Khuddakanikāya",
    "VV": "Khuddakanikāya",
    "VVa": "Khuddakanikāya",
    "PV": "Khuddakanikāya",
    "PVa": "Khuddakanikāya",
    "TH": "Khuddakanikāya",
    "THa": "Khuddakanikāya",
    "THI": "Khuddakanikāya",
    "THIa": "Khuddakanikāya",
    "APA": "Khuddakanikāya",
    "APAa": "Khuddakanikāya",
    "API": "Khuddakanikāya",
    "APIa": "Khuddakanikāya",
    "BV": "Khuddakanikāya",
    "BVa": "Khuddakanikāya",
    "CP": "Khuddakanikāya",
    "CPa": "Khuddakanikāya",
    "JA": "Khuddakanikāya",
    "JAa": "Khuddakanikāya",
    "NIDD1": "Khuddakanikāya",
    "NIDD1a": "Khuddakanikāya",
    "NIDD2": "Khuddakanikāya",
    "NIDD2a": "Khuddakanikāya",
    "PM": "Khuddakanikāya",
    "PMa": "Khuddakanikāya",
    "MIL": "Khuddakanikāya",
    "NP": "Khuddakanikāya",
    "NPa": "Khuddakanikāya",
    "NPt": "Khuddakanikāya",
    "PTP": "Khuddakanikāya",
    # abhidhamma
    "DHS": "Abhidhammapiṭaka",
    "DhS": "Abhidhammapiṭaka",
    "DhSa": "Abhidhammapiṭaka",
    "DHSt": "Abhidhammapiṭaka",
    "DhSṭ": "Abhidhammapiṭaka",
    "VIBH": "Abhidhammapiṭaka",
    "VIBHa": "Abhidhammapiṭaka",
    "VIBHt": "Abhidhammapiṭaka",
    "DHK": "Abhidhammapiṭaka",
    "PP": "Abhidhammapiṭaka",
    "PPa": "Abhidhammapiṭaka",
    "KV": "Abhidhammapiṭaka",
    "YAM": "Abhidhammapiṭaka",
    "PTH": "Abhidhammapiṭaka",
    "ADHa": "Abhidhammapiṭaka",
    "ADHt": "Abhidhammapiṭaka",
    "ADha": "Abhidhammapiṭaka",
    "AdhM": "Abhidhammapiṭaka",
    "ADht": "Abhidhammapiṭaka",
    # post-canonical / aññā — no nikāya prefix
    "VISM": "",
    "VISMa": "",
    "Kacc": "",
    "SPM": "",
    "SDM": "",
    "PRS": "",
    "AP": "",
    "APt": "",
}

# Fallback gui_code -> DPD code, used when file_list doesn't cover the file
# (mostly mul files, which bold_definitions doesn't process).
GUI_TO_DPD: dict[str, str] = {
    "vin1": "VIN",
    "vin2": "VIN",
    "vin3": "VIN",
    "vin4": "VIN",
    "vin5": "VIN",
    "dn1": "DN",
    "dn2": "DN",
    "dn3": "DN",
    "mn1": "MN",
    "mn2": "MN",
    "mn3": "MN",
    "sn1": "SN",
    "sn2": "SN",
    "sn3": "SN",
    "sn4": "SN",
    "sn5": "SN",
    "an1": "AN",
    "an2": "AN",
    "an3": "AN",
    "an4": "AN",
    "an5": "AN",
    "an6": "AN",
    "an7": "AN",
    "an8": "AN",
    "an9": "AN",
    "an10": "AN",
    "an11": "AN",
    "kn1": "KP",
    "kn2": "DHP",
    "kn3": "UD",
    "kn4": "ITI",
    "kn5": "SNP",
    "kn6": "VV",
    "kn7": "PV",
    "kn8": "TH",
    "kn9": "THI",
    "kn10": "APA",
    "kn11": "API",
    "kn12": "BV",
    "kn13": "CP",
    "kn14": "JA",
    "kn15": "NIDD1",
    "kn16": "NIDD2",
    "kn17": "PM",
    "kn18": "MIL",
    "kn19": "NP",
    "kn20": "PTP",
    "abh1": "DHS",
    "abh2": "VIBH",
    "abh3": "DHK",
    "abh4": "PP",
    "abh5": "KV",
    "abh6": "YAM",
    "abh7": "PTH",
}

# Strip leading code prefix from a book_codes display string.
# Examples:
#   "DN1 Sīlakkhandhavagga"           -> "Sīlakkhandhavagga"
#   "1. KP khuddakapāṭha"             -> "khuddakapāṭha"
#   "1a. KPa Khuddakapātha Commentary"-> "Khuddakapātha Commentary"
#   "VINa Commentary"                 -> "Commentary"
#   "ADha Abhidhamma Commentary"      -> "Abhidhamma Commentary"
#   "abhidhānappadīpikā"              -> "abhidhānappadīpikā" (unicode -> no match)
_PREFIX_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\d+[a-z]?\.\s+[A-Za-z][A-Za-z0-9]*\s+"),
    re.compile(r"^[A-Za-z][A-Za-z0-9]*\s+"),
]


def _strip_code_prefix(display: str) -> str:
    for pat in _PREFIX_PATTERNS:
        m = pat.match(display)
        if m:
            return display[m.end() :].strip()
    return display.strip()


def _compose_book_name(dpd_code: str | None, display: str | None) -> str:
    short = _strip_code_prefix(display) if display else ""
    prefix = NIKAYA_PREFIX.get(dpd_code or "", "")
    if prefix and short:
        return f"{prefix}, {short}"
    return prefix or short


def _normalize_pali_case(word: str) -> str:
    """Strip locative -e / nominative -o ending so a stem -a form is used.

    e.g. "Dīghanikāye" -> "Dīghanikāya", "Visuddhimaggo" -> "Visuddhimagga".
    Other endings (-ā, -i, -ī, -u, -ū, -ṃ, consonant) are left alone.
    """
    if word.endswith(("e", "o")):
        return word[:-1] + "a"
    return word


def _read_cst_xml(stem: str) -> str | None:
    path = ProjectPaths().cst_xml_dir / f"{stem}.xml"
    if not path.exists():
        return None
    raw = path.read_bytes()
    for enc in ("utf-16", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def _first_rend(soup: BeautifulSoup, rend: str) -> str | None:
    for tag_name in ("p", "head"):
        tag = soup.find(tag_name, attrs={"rend": rend})
        if tag:
            text = tag.get_text(strip=True)
            if text:
                return text
    return None


# Files where nikaya/book tags are missing and the chapter tag holds a
# category label rather than the book title — the actual book name is the
# first subhead. Without this override the generic chapter-only fallback
# picks up just the label.
_CHAPTER_AS_NIKAYA: set[str] = {"e0906n.nrf", "e0907n.nrf"}

_SPV_TITLE = "Saṃgāyanassa pucchā vissajjanā"


def _is_spv(text: str) -> bool:
    """The Sixth-Council Q&A volumes all share this heading."""
    return "Saṃgāyanassa" in text


def _book_name_from_xml(stem: str) -> tuple[str, str | None]:
    """Return (cst_book_name, dpd_code_override)."""
    text = _read_cst_xml(stem)
    if not text:
        return "", None
    soup = BeautifulSoup(text, "lxml-xml")
    nikaya = _first_rend(soup, "nikaya")
    book = _first_rend(soup, "book")
    spv = _is_spv(text)
    if not nikaya and not book:
        if stem in _CHAPTER_AS_NIKAYA:
            nikaya = _first_rend(soup, "chapter")
            book = _first_rend(soup, "subhead")
        else:
            book = _first_rend(soup, "chapter")
    elif spv and nikaya and not book:
        # SPV files sometimes record the nikāya in <p rend="chapter">.
        book = _first_rend(soup, "chapter")
    parts = [
        _normalize_pali_case(_strip_trailing_punct(p)) for p in (nikaya, book) if p
    ]
    if spv:
        # Drop the Q&A subhead so we don't print SPV twice, then prepend
        # the canonical SPV title as the leading work name.
        parts = [p for p in parts if "Saṃgāyana" not in p]
        parts.insert(0, _SPV_TITLE)
    name = ", ".join(parts)
    return name, ("SPV" if spv else None)


def _strip_trailing_punct(text: str) -> str:
    return text.rstrip(" .,;:")


def _gui_display_for(gui_code: str | None) -> str | None:
    if not gui_code:
        return None
    for display, code in book_codes.items():
        if code == gui_code:
            return display
    return None


def build_rows() -> list[dict[str, str]]:
    # Invert cst_texts: txt filename stem -> gui_code.
    # cst_texts values are like ["s0101m.mul.txt"]; strip ".txt" to get the stem.
    txt_to_gui: dict[str, str] = {}
    for gui_code, txt_files in cst_texts.items():
        for txt_name in txt_files:
            stem = txt_name[:-4] if txt_name.endswith(".txt") else txt_name
            txt_to_gui[stem] = gui_code

    # file_list keys are xml filenames; strip ".xml" to get the stem.
    xml_to_dpd: dict[str, str] = {}
    for xml_name, dpd_code in file_list.items():
        stem = xml_name[:-4] if xml_name.endswith(".xml") else xml_name
        xml_to_dpd[stem] = dpd_code

    all_stems = sorted(set(txt_to_gui) | set(xml_to_dpd))
    rows: list[dict[str, str]] = []
    for stem in all_stems:
        gui_code = txt_to_gui.get(stem)
        dpd_code = xml_to_dpd.get(stem) or GUI_TO_DPD.get(gui_code or "")
        book_name, dpd_override = _book_name_from_xml(stem)
        if dpd_override:
            dpd_code = dpd_override
        if not book_name:
            book_name = _compose_book_name(dpd_code, _gui_display_for(gui_code))
        rows.append(
            {
                "cst_filename": stem,
                "cst_book_name": book_name,
                "gui_book_code": gui_code or "",
                "dpd_book_code": dpd_code or "",
            }
        )
    return rows


def main() -> None:
    out_path = Path("tools/cst_book_translator.tsv")
    rows = build_rows()
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "cst_filename",
                "cst_book_name",
                "gui_book_code",
                "dpd_book_code",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
