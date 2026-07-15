#!/usr/bin/env python3

"""
Calculate the number of occurrences of a word's inflections
in early texts across all four corpora (CST, BJT, SC, SYA) and add to db.
Takes the maximum frequency across corpora.
"""

import json
import os
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_text_files import bjt_texts, cst_texts, ebts, sc_texts
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def _sya_is_ebt(key: str) -> bool:
    """Check if SYA file key is EBT.

    Include: 01-02 (Monks' Vibhaṅga = VIN1+VIN2 equivalent)
             09-25 (DN, MN, SN, AN, and KN small texts = kn1-5+kn8-9 combined in Khu_Khu)
    Exclude: 03-08 (Bhikkhunī Vibhaṅga, Mahāvagga, Cullavagga, Parivāra)
             26-33 (Vimānavatthu, Jātaka, Niddesa, Paṭisambhidāmagga, Apadāna)
             34-45 (Abhidhamma)
    """
    if not key.startswith("canon/"):
        return False
    try:
        num = int(key.split("/")[1].split("_")[0])
        return num <= 2 or (9 <= num <= 25)
    except (IndexError, ValueError):
        return False


def _merge_ebt_freq(
    freq: dict[str, dict[str, int]],
    ebt_keys: list[str],
) -> dict[str, int]:
    """Merge EBT file frequency dicts into one summed dict."""
    merged: dict[str, int] = {}
    for key in ebt_keys:
        for word, count in freq.get(key, {}).items():
            merged[word] = merged.get(word, 0) + count
    return merged


def main() -> None:
    pr.tic()
    pr.yellow_title("calculating frequency in ebts")
    pr.green_tmr("setting up")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Load all four corpus frequency dicts
    with pth.cst_file_freq.open(encoding="utf-8") as f:
        cst_freq: dict[str, dict[str, int]] = json.load(f)
    with pth.bjt_file_freq.open(encoding="utf-8") as f:
        bjt_freq: dict[str, dict[str, int]] = json.load(f)
    with pth.sc_file_freq.open(encoding="utf-8") as f:
        sc_freq: dict[str, dict[str, int]] = json.load(f)
    with pth.sya_file_freq.open(encoding="utf-8") as f:
        sya_freq: dict[str, dict[str, int]] = json.load(f)

    db = db_session.query(DpdHeadword).all()

    # Derive EBT book keys from ebts list and cst_texts
    cst_file_to_book: dict[str, str] = {
        f: book for book, files in cst_texts.items() for f in files
    }
    ebt_books: set[str] = {cst_file_to_book[f] for f in ebts if f in cst_file_to_book}

    # Build per-corpus EBT file key lists
    cst_ebt_keys: list[str] = [f.replace(".txt", ".xml") for f in ebts]
    bjt_ebt_keys: list[str] = [f for book in ebt_books for f in bjt_texts.get(book, [])]

    sc_ebt_basenames: set[str] = {
        f for book in ebt_books for f in sc_texts.get(book, [])
    }
    sc_ebt_keys: list[str] = [k for k in sc_freq if Path(k).name in sc_ebt_basenames]

    sya_ebt_keys: list[str] = [k for k in sya_freq if _sya_is_ebt(k)]

    # Pre-merge EBT files into single dicts (one-time cost; makes main loop fast)
    cst_merged = _merge_ebt_freq(cst_freq, cst_ebt_keys)
    bjt_merged = _merge_ebt_freq(bjt_freq, bjt_ebt_keys)
    sc_merged = _merge_ebt_freq(sc_freq, sc_ebt_keys)
    sya_merged = _merge_ebt_freq(sya_freq, sya_ebt_keys)

    pr.yes("ok")

    # Debug mode: show old vs new counts for first N headwords (set via DEBUG_N env var)
    debug_n = int(os.environ.get("DEBUG_N", "0"))
    if debug_n > 0:
        pr.yellow_title(f"debug: showing counts for first {debug_n} headwords")

    pr.green_tmr("calculating")
    for idx, i in enumerate(db):
        old_count: int = i.ebt_count or 0
        inflections: list[str] = i.inflections_list_all
        cst_total = sum(cst_merged.get(inf, 0) for inf in inflections)
        bjt_total = sum(bjt_merged.get(inf, 0) for inf in inflections)
        sc_total = sum(sc_merged.get(inf, 0) for inf in inflections)
        sya_total = sum(sya_merged.get(inf, 0) for inf in inflections)
        i.ebt_count = max(cst_total, bjt_total, sc_total, sya_total)

        # Debug output
        if debug_n > 0 and idx < debug_n:
            pr.green(
                f"#{idx + 1:5d} {i.lemma_1:<30} "
                f"old:{old_count:6d} → new:{i.ebt_count:6d}  "
                f"(cst:{cst_total:6d} bjt:{bjt_total:6d} sc:{sc_total:6d} sya:{sya_total:6d})"
            )

    pr.yes("ok")

    pr.green_tmr("saving to db")
    db_session.commit()
    pr.yes("ok")

    pr.toc()


if __name__ == "__main__":
    main()
