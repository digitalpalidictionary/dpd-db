# -*- coding: utf-8 -*-
from collections import defaultdict, namedtuple
from functools import cached_property
from json import load
from pathlib import Path

from tools.clean_machine import clean_machine
from tools.pali_alphabet import pali_alphabet
from tools.sort_naturally import natural_sort

SuttaCentralSegment = namedtuple("SuttaCentralSegment", ["segment", "pali", "english"])


class SuttaCentralSource:
    def __init__(
        self,
        book: str,
        cst_books: list[str],
        pali_path: str | None,
        english_path: str | None,
        is_commentary: bool,
    ) -> None:
        self.sc_book: str = book
        self.is_commentary: bool = is_commentary
        self.cst_books: list[str] = cst_books
        self.pali_path: Path | None = Path(pali_path) if pali_path else None
        self.english_path: Path | None = Path(english_path) if english_path else None

        self.pali_file_list: list[Path] = (
            self.make_file_list(self.pali_path) if self.pali_path else []
        )
        self.english_file_list: list[Path] = (
            self.make_file_list(self.english_path) if self.english_path else []
        )
        self.allowable_chars: list[str] = pali_alphabet + [" "]

    def make_file_list(self, folder: Path | None) -> list[Path]:
        if not folder or not folder.exists() or not folder.is_dir():
            return []
        return natural_sort([p for p in folder.rglob("*") if p.is_file()])

    @cached_property
    def segment_dict(self) -> dict[str, SuttaCentralSegment]:
        segment_dict: dict[str, SuttaCentralSegment] = {}
        if self.pali_file_list:
            for file_path in self.pali_file_list:
                data: dict[str, str] = load(file_path.open("r", encoding="utf-8"))
                for segment, sentence in data.items():
                    sentence = sentence.replace("ṁ", "ṃ").lower()
                    segment_dict[segment] = SuttaCentralSegment(segment, sentence, "")

        if self.english_file_list:
            for file_path in self.english_file_list:
                data: dict[str, str] = load(file_path.open("r", encoding="utf-8"))
                for segment, sentence in data.items():
                    if segment in segment_dict:
                        current = segment_dict[segment]
                        segment_dict[segment] = SuttaCentralSegment(
                            current.segment, current.pali, sentence
                        )
                    else:
                        # sometimes only english exists
                        segment_dict[segment] = SuttaCentralSegment(
                            segment, "", sentence
                        )
        return segment_dict

    @cached_property
    def word_dict(self) -> defaultdict[str, list[SuttaCentralSegment]]:
        word_dict: defaultdict[str, list[SuttaCentralSegment]] = defaultdict(list)
        for segment in self.segment_dict.values():
            pali: str = clean_machine(segment.pali)
            for word in pali.split():
                word_dict[word].append(segment)
        return word_dict


sutta_central_books: dict[str, SuttaCentralSource] = {
    "vin1&2": SuttaCentralSource(
        "vin1&2",
        ["vin1", "vin2"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/vinaya/pli-tv-bu-vb",
        "resources/sc-data/sc_bilara_data/translation/en/brahmali/vinaya/pli-tv-bu-vb",
        is_commentary=False,
    ),
    "vin-bi": SuttaCentralSource(
        "vin-bi",
        ["vin2"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/vinaya/pli-tv-bi-vb",
        "resources/sc-data/sc_bilara_data/translation/en/brahmali/vinaya/pli-tv-bi-vb",
        is_commentary=False,
    ),
    "vin3&4": SuttaCentralSource(
        "vin3&4",
        ["vin3", "vin4"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/vinaya/pli-tv-kd",
        "resources/sc-data/sc_bilara_data/translation/en/brahmali/vinaya/pli-tv-kd",
        is_commentary=False,
    ),
    "vin5": SuttaCentralSource(
        "vin5",
        ["vin5"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/vinaya/pli-tv-pvr",
        "resources/sc-data/sc_bilara_data/translation/en/brahmali/vinaya/pli-tv-pvr",
        is_commentary=False,
    ),
    "dn": SuttaCentralSource(
        "dn",
        ["dn3", "dn1", "dn2"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/dn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/dn",
        is_commentary=False,
    ),
    "mn": SuttaCentralSource(
        "mn",
        ["mn3", "mn2", "mn1"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/mn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/mn",
        is_commentary=False,
    ),
    "sn": SuttaCentralSource(
        "sn",
        ["sn1", "sn2", "sn3", "sn4", "sn5"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/sn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/sn",
        is_commentary=False,
    ),
    "an": SuttaCentralSource(
        "an",
        ["an1", "an2", "an3", "an4", "an5", "an6", "an7", "an8", "an9", "an10", "an11"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/an",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/an",
        is_commentary=False,
    ),
    "khp": SuttaCentralSource(
        "khp",
        ["kn1"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/kp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/kp",
        is_commentary=False,
    ),
    "dhp": SuttaCentralSource(
        "dhp",
        ["kn2"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/dhp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/dhp",
        is_commentary=False,
    ),
    "ud": SuttaCentralSource(
        "ud",
        ["kn3"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ud",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ud",
        is_commentary=False,
    ),
    "iti": SuttaCentralSource(
        "iti",
        ["kn4"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/iti",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/iti",
        is_commentary=False,
    ),
    "snp": SuttaCentralSource(
        "snp",
        ["kn5"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/snp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/snp",
        is_commentary=False,
    ),
    "th": SuttaCentralSource(
        "th",
        ["kn8"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/thag",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/thag",
        is_commentary=False,
    ),
    "thi": SuttaCentralSource(
        "thi",
        ["kn9"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/thig",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/thig",
        is_commentary=False,
    ),
    "cp": SuttaCentralSource(
        "cp",
        ["kn13"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/cp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/cp",
        is_commentary=False,
    ),
    "ja": SuttaCentralSource(
        "ja",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
        is_commentary=False,
    ),
    "nidd1&2": SuttaCentralSource(
        "nidd1&2",
        ["kn15", "kn16"],
        None,
        None,
        is_commentary=False,
    ),
    "kva": SuttaCentralSource(
        "kva",
        ["kva"],
        None,
        None,
        is_commentary=True,
    ),
    "dhpa": SuttaCentralSource(
        "dhpa",
        ["kn2a"],
        None,
        None,
        is_commentary=True,
    ),
    "jaa": SuttaCentralSource(
        "jaa",
        ["kn14a"],
        None,
        None,
        is_commentary=True,
    ),
    "dna": SuttaCentralSource(
        "dna",
        ["dna"],
        None,
        None,
        is_commentary=True,
    ),
}
