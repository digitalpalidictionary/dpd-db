#!/usr/bin/env python3.10

# sandhi paths

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ResourcePaths:
    cst_txt_dir: Path
    cst_xml_dir: Path
    raw_text_dir: Path
    word_count_dir: Path
    tipitaka_raw_text_path: Path
    tipitaka_word_count_path: Path
    ebt_raw_text_path: Path
    ebt_word_count_path: Path


def get_paths() -> ResourcePaths:
    pth = ResourcePaths(
        cst_txt_dir=Path(
            "../Cst4/txt"),
        cst_xml_dir=Path(
            "../Cst4/Xml"),
        raw_text_dir=Path(
            "frequency/output/raw_text/"),
        word_count_dir=Path(
            "frequency/output/word_count"),
        tipitaka_raw_text_path=Path(
            "frequency/output/raw_text/tipitaka.txt"),
        tipitaka_word_count_path=Path(
            "frequency/output/word_count/tipitaka.csv"),
        ebt_raw_text_path=Path(
            "frequency/output/raw_text/ebts.txt"),
        ebt_word_count_path=Path(
            "frequency/output/word_count/ebts.csv"),
    )

    # ensure dirs exist
    for d in [
        pth.raw_text_dir,
        pth.word_count_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    return pth
