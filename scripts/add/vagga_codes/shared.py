"""Shared helpers for vagga sutta-code enrichment.

No DB writes occur anywhere in this package — output is TSV previews only.
"""

from __future__ import annotations

import csv
import re
from collections import OrderedDict
from pathlib import Path

SUTTA_INFO_TSV = Path("db/backup_tsv/sutta_info.tsv")
PREVIEW_DIR = Path("temp")

VaggaKey = tuple[str, str | None]
# (first_dpd_code, last_dpd_code, cst_vagga_name, cst_chapter_num_or_None)
VaggaRun = tuple[str, str, str, int | None]

CHAPTER_RE = re.compile(r"(?:Chapter|Section)\s+(\d+)")
CST_VAGGA_LEAD_RE = re.compile(r"^\s*(\d+)\.\s*")
DPD_CODE_RE = re.compile(r"^([A-Za-z]+)(\d+)(?:\.(\d+))?")
TRAILING_CODE_RE = re.compile(r"\s*\([A-Za-z]+\d+(?:\.\d+)?(?:-\d+)?\)\s*$")
ANY_CODE_RE = re.compile(r"\(([A-Za-z]+\d+(?:\.\d+)?(?:-(?:\d+\.)?\d+)?)\)")


def load_vagga_runs(
    tsv_path: Path = SUTTA_INFO_TSV,
) -> dict[VaggaKey, list[VaggaRun]]:
    """Build map `(book_code, inner_section) -> ordered list of vagga runs`.

    `inner_section` is the numeric part before the dot in `dpd_code` (e.g. `SN1.1`
    → `"1"`). Books without a sub-section (e.g. `MN1`) use `inner_section = None`.

    A "vagga run" is a contiguous span of suttas sharing the same `cst_vagga`
    within its `(book, inner)` group, in TSV order. Vagga runs are position-
    indexed (1-based) to match DPD `meaning_1`'s `"Chapter N"`.
    """
    # state per (book, inner): [current_vagga_name, runs_list_of_lists_of_codes]
    state: "OrderedDict[VaggaKey, tuple[str | None, list[list[str]], list[str]]]" = (
        OrderedDict()
    )

    with tsv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            dpd_code = (row.get("dpd_code") or "").strip()
            cst_vagga = (row.get("cst_vagga") or "").strip()
            book_code = (row.get("book_code") or "").strip()
            if not dpd_code or not cst_vagga or not book_code:
                continue
            m_code = DPD_CODE_RE.match(dpd_code)
            if not m_code:
                continue
            _, first_num, second_num = m_code.groups()
            inner = first_num if second_num else None
            key: VaggaKey = (book_code, inner)

            entry = state.get(key)
            if entry is None:
                state[key] = (cst_vagga, [[dpd_code]], [cst_vagga])
                continue
            cur_name, runs, names = entry
            if cst_vagga == cur_name:
                runs[-1].append(dpd_code)
            else:
                runs.append([dpd_code])
                names.append(cst_vagga)
            state[key] = (cst_vagga, runs, names)

    result: dict[VaggaKey, list[VaggaRun]] = {}
    for key, (_, runs, names) in state.items():
        run_list: list[VaggaRun] = []
        for codes, name in zip(runs, names):
            m = CST_VAGGA_LEAD_RE.match(name)
            ch = int(m.group(1)) if m else None
            run_list.append((codes[0], codes[-1], name, ch))
        result[key] = run_list
    return result


def load_section_spans(
    tsv_path: Path = SUTTA_INFO_TSV,
) -> dict[VaggaKey, tuple[str, str]]:
    """Build map `(book_code, inner_section) -> (first_dpd_code, last_dpd_code)`.

    Spans every sutta of a (book, inner) regardless of `cst_vagga`. Used as a
    fallback for samyuttas/sections whose TSV rows have empty `cst_vagga`
    (single-vagga samyuttas where the whole section is one vagga).
    """
    state: "OrderedDict[VaggaKey, list[str]]" = OrderedDict()
    with tsv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            dpd_code = (row.get("dpd_code") or "").strip()
            book_code = (row.get("book_code") or "").strip()
            if not dpd_code or not book_code:
                continue
            m_code = DPD_CODE_RE.match(dpd_code)
            if not m_code:
                continue
            _, first_num, second_num = m_code.groups()
            inner = first_num if second_num else None
            state.setdefault((book_code, inner), []).append(dpd_code)
    return {k: (v[0], v[-1]) for k, v in state.items()}


LAST_NUM_RE = re.compile(r"(\d+)(?!.*\d)")


def _last_sutta_num(code: str) -> str:
    """Return the terminal sutta number, respecting hyphen ranges like `SN31.23-112`."""
    m = LAST_NUM_RE.search(code)
    return m.group(1) if m else ""


def format_range(book_code: str, first_code: str, last_code: str) -> str:
    """Format a sutta-code range per book-specific conventions.

    - `MN`/single-segment codes: `"MN1-10"`
    - `SN`/`AN`/two-segment codes: `"SN1.1-10"`, `"AN3.1-10"`
    Handles hyphenated dpd_codes (e.g. `SN31.23-112` → terminal `112`).
    """
    m1 = DPD_CODE_RE.match(first_code)
    m2 = DPD_CODE_RE.match(last_code)
    if not m1 or not m2:
        raise ValueError(f"Unparseable dpd_code(s): {first_code!r}, {last_code!r}")
    _, a1, b1 = m1.groups()
    _, a2, _ = m2.groups()
    last_num = _last_sutta_num(last_code)
    if b1 is not None:
        if a1 == a2:
            return f"{book_code}{a1}.{b1}-{last_num}"
        return f"{book_code}{a1}.{b1}-{a2}.{last_num}"
    if a1 == a2:
        return f"{book_code}{a1}"
    return f"{book_code}{a1}-{last_num}"


def parse_chapter(meaning: str | None) -> int | None:
    if not meaning:
        return None
    m = CHAPTER_RE.search(meaning)
    return int(m.group(1)) if m else None


CHAPTER_WORD_RE = re.compile(r"\b(C|c)(hapter)(s?)\b")
VAGGAS_OF_THE_RE = re.compile(r"\bvaggas of the\b")


def chapter_to_vagga(text: str | None) -> str:
    """Replace `chapter(s)` / `Chapter(s)` with `vagga(s)` / `Vagga(s)`."""
    if not text:
        return text or ""
    return CHAPTER_WORD_RE.sub(
        lambda m: ("V" if m.group(1) == "C" else "v") + "agga" + m.group(3), text
    )


def chapter_to_section(text: str | None) -> str:
    """Replace `chapter(s)` / `Chapter(s)` with `section(s)` / `Section(s)`.

    Used for `meaning_lit` where `vagga` would be out of place (meaning_lit
    is an English literal gloss, not the Pāḷi structural term).
    """
    if not text:
        return text or ""
    return CHAPTER_WORD_RE.sub(
        lambda m: ("S" if m.group(1) == "C" else "s") + "ection" + m.group(3),
        text,
    )


def normalize_family_set(text: str | None) -> str:
    """Apply chapter→vagga and strip redundant `the` in `vaggas of the …`."""
    if not text:
        return text or ""
    return VAGGAS_OF_THE_RE.sub("vaggas of", chapter_to_vagga(text))


def strip_trailing_code(text: str) -> str:
    """Remove a trailing `" (ABC1.2-3)"` if present; leaves other parentheticals."""
    if not text:
        return text
    return TRAILING_CODE_RE.sub("", text).rstrip()


_NAT_SPLIT = re.compile(r"(\d+)")


def _sort_key(row: dict) -> list:
    text = row.get("new_meaning_1") or row.get("old_meaning_1") or ""
    return [int(t) if t.isdigit() else t for t in _NAT_SPLIT.split(text)]


def write_preview_tsv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "lemma_1",
        "old_family_set",
        "new_family_set",
        "old_meaning_1",
        "new_meaning_1",
        "old_meaning_lit",
        "new_meaning_lit",
        "status",
    ]
    sorted_rows = sorted(rows, key=_sort_key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for r in sorted_rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
