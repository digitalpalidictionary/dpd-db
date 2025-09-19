# -*- coding: utf-8 -*-
from collections import defaultdict, namedtuple
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
    ) -> None:
        self.sc_book: str = book
        self.cst_books: list[str] = cst_books
        self.pali_path: Path | None = Path(pali_path) if pali_path else None
        self.english_path: Path | None = Path(english_path) if english_path else None

        self.pali_file_list: list[Path] = (
            self.make_file_list(self.pali_path) if self.pali_path else []
        )
        self.english_file_list: list[Path] = (
            self.make_file_list(self.english_path) if self.english_path else []
        )

        self.segment_dict: dict[str, SuttaCentralSegment] = {}
        self.make_segment_dict()

        self.word_dict: defaultdict[str, list[SuttaCentralSegment]] = defaultdict(list)
        self.allowable_chars: list[str] = pali_alphabet + [" "]
        self.process_words()

        # print(self.word_dict["virāgo"])

    def make_file_list(self, folder: Path | None) -> list[Path]:
        if not folder or not folder.exists() or not folder.is_dir():
            return []
        return natural_sort([p for p in folder.rglob("*") if p.is_file()])

    def make_segment_dict(self) -> None:
        if self.pali_file_list:
            for file_path in self.pali_file_list:
                data: dict[str, str] = load(file_path.open("r", encoding="utf-8"))
                for segment, sentence in data.items():
                    sentence = sentence.replace("ṁ", "ṃ").lower()
                    self.segment_dict[segment] = SuttaCentralSegment(
                        segment, sentence, ""
                    )

        if self.english_file_list:
            for file_path in self.english_file_list:
                data: dict[str, str] = load(file_path.open("r", encoding="utf-8"))
                for segment, sentence in data.items():
                    if segment in self.segment_dict:
                        current = self.segment_dict[segment]
                        self.segment_dict[segment] = SuttaCentralSegment(
                            current.segment, current.pali, sentence
                        )
                    else:
                        # sometimes only english exists
                        self.segment_dict[segment] = SuttaCentralSegment(
                            segment, "", sentence
                        )

    def process_words(self) -> None:
        for segment in self.segment_dict.values():
            pali: str = clean_machine(segment.pali)
            for word in pali.split():
                self.word_dict[word].append(segment)


sutta_central_books: dict[str, SuttaCentralSource] = {
    "vin3&4": SuttaCentralSource(
        "vin3&4",
        ["vin3", "vin4"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/vinaya/pli-tv-kd",
        "resources/sc-data/sc_bilara_data/translation/en/brahmali/vinaya/pli-tv-kd",
    ),
    "vin5": SuttaCentralSource(
        "vin5",
        ["vin5"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/vinaya/pli-tv-pvr",
        "resources/sc-data/sc_bilara_data/translation/en/brahmali/vinaya/pli-tv-pvr",
    ),
    "dn": SuttaCentralSource(
        "dn",
        ["dn3", "dn1", "dn2"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/dn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/dn",
    ),
    "mn": SuttaCentralSource(
        "mn",
        ["mn3", "mn2", "mn1"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/mn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/mn",
    ),
    "sn": SuttaCentralSource(
        "sn",
        ["sn1", "sn2", "sn3", "sn4", "sn5"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/sn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/sn",
    ),
    "an": SuttaCentralSource(
        "an",
        ["an1", "an2", "an3", "an4", "an5", "an6", "an7", "an8", "an9", "an10", "an11"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/an",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/an",
    ),
    "khp": SuttaCentralSource(
        "khp",
        ["kn1"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/kp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/kp",
    ),
    "dhp": SuttaCentralSource(
        "dhp",
        ["kn2"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/dhp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/dhp",
    ),
    "ud": SuttaCentralSource(
        "ud",
        ["kn3"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ud",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ud",
    ),
    "iti": SuttaCentralSource(
        "iti",
        ["kn4"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/iti",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/iti",
    ),
    "snp": SuttaCentralSource(
        "snp",
        ["kn5"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/snp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/snp",
    ),
    "th": SuttaCentralSource(
        "th",
        ["kn8"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/thag",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/thag",
    ),
    "thi": SuttaCentralSource(
        "thi",
        ["kn9"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/thig",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/thig",
    ),
    "cp": SuttaCentralSource(
        "cp",
        ["kn13"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/cp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/cp",
    ),
    "ja": SuttaCentralSource(
        "ja",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
    ),
    "dhpa": SuttaCentralSource(
        "dhpa",
        ["kn14a"],
        None,
        None,
    ),
}
