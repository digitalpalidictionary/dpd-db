"""Extract variants readings from Syāmaraṭṭḥa (Thai) texts."""

import re
from dataclasses import dataclass
from pathlib import Path

from icecream import ic

from db.variants.files_to_books import sya_files_to_books
from db.variants.variants_modules import (
    VariantsDict,
    context_cleaner,
    key_cleaner,
    normalize_pali_text,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr

debug = False

_PAGE_SPLIT_RE = re.compile(r"(?=page number: \d+)")
_PAGE_NUM_RE = re.compile(r"page number: (\d+)")
_PAGE_VAR_RE = re.compile(
    r"""
    (
        (?:[^ ]+\s+)?   # optional first word followed by space
        [^ ]+           # one or more characters without space (capture group 1)
    )
    \s                  # a space
    \[*                 # 0+ opening square brackets
    (\d+)               # 1+ digits (capture group 2)
    \]*                 # 0+ closing square brackets
    -                   # dash
    """,
    re.VERBOSE,
)
_FOOTNOTE_SECTION_RE = re.compile(r"footnote:(.*?)(?=\n-{2,}|$)", re.DOTALL)
_FOOTNOTE_SPLIT_RE = re.compile(r"(?<=\.)* +(?=\d)")
_TRIPLE_RANGE_RE = re.compile(r"\d+-\d+-\d+")
_TRIPLE_RANGE_CAPTURE_RE = re.compile(r"(\d+)-\d+-(\d+)")
_DOUBLE_RANGE_RE = re.compile(r"\d+-\d+")
_DOUBLE_RANGE_CAPTURE_RE = re.compile(r"(\d+)-(\d+)")
_NORMAL_FOOTNOTE_RE = re.compile(r"^(\d+)\s(.+)")
_DASHES_RE = re.compile(r"-{3,}")


@dataclass
class _SyaStats:
    successes: int = 0
    errors: int = 0


def process_sya(variants_dict: VariantsDict, pth: ProjectPaths) -> VariantsDict:
    pr.green_title("extracting variants from SYA texts")

    file_list: list[Path] = get_sya_file_list(pth)
    stats = _SyaStats()

    for counter, file_name in enumerate(file_list):
        if counter % 20 == 0:
            pr.counter(counter, len(file_list), file_name.name)

        book = sya_files_to_books.get(file_name.name)
        if book is None:
            continue
        text = get_sya_text(file_name)
        variants_dict = extract_sya_variants(book, text, variants_dict, stats)

    error_rate = (stats.errors / stats.successes * 100) if stats.successes else 0.0
    pr.red(f"extracted:  {stats.successes - stats.errors} / {stats.successes}")
    pr.red(f"error rate: {error_rate:.2f}%")

    return variants_dict


def get_sya_file_list(pth: ProjectPaths) -> list[Path]:
    """Get a list of all SYA variants files."""

    # only the corrected corpus — the raw, decoder-corrupted rip under txt/ carries
    # identical filenames and must never be picked up
    corpus_dirs = [pth.sya_dir / "Canonical", pth.sya_dir / "Non-Canonical"]
    sya_sort_order = {filename: idx for idx, filename in enumerate(sya_files_to_books)}
    all_files = [
        file
        for corpus_dir in corpus_dirs
        for file in corpus_dir.glob("*.txt")
        if file.is_file()
    ]
    file_list = sorted(
        all_files,
        key=lambda x: sya_sort_order.get(x.name, float("inf")),
    )
    return file_list


def get_sya_text(file_name: Path) -> str:
    with file_name.open("r", encoding="utf-8-sig") as f:
        text = f.read()

        # remove new lines
        text = text.replace("\n", " ")

        # remove PTS cross-references e.g. (pts. d i, 2)
        text = re.sub(r"\(pts[^)]*\)", "", text)

        # remove multiple space
        text = re.sub(" +", " ", text)

        text = normalize_pali_text(text)

        return text


def get_page_number(page: str) -> int:
    """Find the page number."""

    page_match = _PAGE_NUM_RE.search(page)
    if page_match:
        return int(page_match.group(1))
    else:
        return 0


def extract_sya_variants(
    book: str, text: str, variants_dict: VariantsDict, stats: _SyaStats
) -> VariantsDict:
    """Extract variants from a SYA text file."""

    pages = _PAGE_SPLIT_RE.split(text)

    for page in pages:
        page_num: int = get_page_number(page)
        page_vars = get_variants_in_page(page)
        footnote_vars = get_variants_in_footnotes(page)

        if len(footnote_vars) != len(page_vars):
            stats.errors += 1
            if debug:
                ic(book)
                ic(page_num)
                ic(page_vars)
                ic(footnote_vars)
                ic(len(footnote_vars) == len(page_vars))
                pr.white("")

        for var_num, context in page_vars.items():
            word = context.split(" ")[-1]
            word_clean = key_cleaner(word)
            if not word_clean:
                continue
            context_clean = context_cleaner(context)

            variant_raw = footnote_vars.get(var_num)
            if variant_raw is None:
                if debug:
                    ic("missing footnote")
                    ic(book)
                    ic(word_clean)
                    ic(var_num)
                    pr.white("")
                continue
            variant = variant_raw.strip()

            variants_dict.setdefault(word_clean, {}).setdefault("SYA", {}).setdefault(
                book, []
            ).append((context_clean, variant.lower()))
            stats.successes += 1

    return variants_dict


def get_variants_in_page(text: str) -> dict[str, str]:
    """Find variants in the page"""

    page_vars: dict[str, str] = {}
    matches = _PAGE_VAR_RE.findall(text)
    for context, number in matches:
        page_vars[number] = context
    return page_vars


def clean_variant(text: str) -> str:
    """remove -------"""
    return _DASHES_RE.sub("", text).strip()


def get_variants_in_footnotes(page: str) -> dict[str, str]:
    """Find variants in the footnotes"""

    # Footnote:1 ayaṁ pāṭho katthaci na dissati. 2 sāvakānantipi atthi.

    footnote_vars: dict[str, str] = {}

    # isolate the footnote section
    section_match = _FOOTNOTE_SECTION_RE.search(page)
    if section_match:
        footnote_str = section_match.group(1).strip()

        # a page may carry more than one footnote block; drop residual labels
        # so the marker word cannot leak into a variant reading
        footnote_str = footnote_str.replace("footnote:", " ")

        # split on 0+ dot behind / 1 or more spaces / number ahead
        footnotes = _FOOTNOTE_SPLIT_RE.split(footnote_str)
        for footnote in footnotes:
            # footnote contains a triple range e.g.
            # 3-4-5 yamidha sañjotibhūtā sañjotibhūto sañjotibhūtanti likhiyati
            if _TRIPLE_RANGE_RE.search(footnote):
                triple_match = _TRIPLE_RANGE_CAPTURE_RE.search(footnote)
                if triple_match:
                    start, end = triple_match.group(1), triple_match.group(2)
                    if start and end:
                        variant = _TRIPLE_RANGE_CAPTURE_RE.sub("", footnote)
                        variant = clean_variant(variant)
                        for i in range(int(start), int(end) + 1):
                            footnote_vars[str(i)] = variant
                            if debug:
                                ic(str(i), variant)
                                pr.white("")

            # footnote contains a number range e.g.
            # 1-3 Yu. Ma. arahattaṁ.
            elif _DOUBLE_RANGE_RE.search(footnote):
                double_match = _DOUBLE_RANGE_CAPTURE_RE.search(footnote)
                if double_match:
                    start, end = double_match.group(1), double_match.group(2)
                    if start and end:
                        variant = _DOUBLE_RANGE_CAPTURE_RE.sub("", footnote)
                        variant = clean_variant(variant)
                        for i in range(int(start), int(end) + 1):
                            footnote_vars[str(i)] = variant
                            if debug:
                                ic(str(i), variant)
                                pr.white("")

            # normal situation
            else:
                matches = _NORMAL_FOOTNOTE_RE.findall(footnote)
                for number, variant in matches:
                    variant = clean_variant(variant)
                    footnote_vars[number] = variant

    return footnote_vars


# TODO issues
# -* in text and footnotes
# missing footnotes in text
