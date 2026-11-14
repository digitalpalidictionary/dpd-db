# -*- coding: utf-8 -*-
from collections import defaultdict, namedtuple
from functools import cached_property
from json import load
from pathlib import Path
from re import match, sub

from tools.clean_machine import clean_machine
from tools.pali_alphabet import pali_alphabet
from tools.sort_naturally import natural_sort

SuttaCentralSegment = namedtuple("SuttaCentralSegment", ["segment", "pali", "english"])


class SuttaCentralSource:
    def __init__(
        self,
        book: str,
        cst_books: list[str],
        pali_path: str | list[str] | None,
        english_path: str | list[str] | None,
        is_commentary: bool,
        story_range: range | None = None,
    ) -> None:
        self.sc_book: str = book
        self.is_commentary: bool = is_commentary
        self.story_range: range | None = story_range
        self.cst_books: list[str] = cst_books
        self.pali_paths: list[Path] = self.to_paths(pali_path)
        self.english_paths: list[Path] = self.to_paths(english_path)

        self.pali_file_list: list[Path] = self.make_file_lists(self.pali_paths)
        self.english_file_list: list[Path] = self.make_file_lists(self.english_paths)
        self.allowable_chars: list[str] = pali_alphabet + [" "]

    @staticmethod
    def to_paths(path: str | list[str] | None) -> list[Path]:
        if not path:
            return []
        return [Path(p) for p in ([path] if isinstance(path, str) else path)]

    def make_file_lists(self, folders: list[Path]) -> list[Path]:
        # the files of all folders are sorted together, as one text
        return natural_sort(
            [p for folder in folders for p in self.make_file_list(folder)]
        )

    def make_file_list(self, folder: Path | None) -> list[Path]:
        if not folder or not folder.exists() or not folder.is_dir():
            return []
        files = [p for p in folder.rglob("*") if p.is_file()]
        if self.story_range is not None:
            # SuttaCentral names a story's file by its number: ja123_root-pli-ms.json
            files = [
                p
                for p in files
                if (m := match(r"\D*(\d+)_", p.name))
                and int(m.group(1)) in self.story_range
            ]
        return natural_sort(files)

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
            # SC bolds a quoted word and leaves the closing "ti" outside the tag:
            # "<b>agāran</b>ti". Splitting at the tag makes junk words.
            pali: str = clean_machine(sub(r"</?b>", "", segment.pali))
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
    "vv": SuttaCentralSource(
        "vv",
        ["kn6"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/vv",
        None,
        is_commentary=False,
    ),
    "pv": SuttaCentralSource(
        "pv",
        ["kn7"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/pv",
        "resources/sc-data/sc_bilara_data/translation/en/kovilo/sutta/kn/pv",
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
    "tha-ap": SuttaCentralSource(
        "tha-ap",
        ["kn10"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/tha-ap",
        None,
        is_commentary=False,
    ),
    "thi-ap": SuttaCentralSource(
        "thi-ap",
        ["kn11"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/thi-ap",
        None,
        is_commentary=False,
    ),
    "bv": SuttaCentralSource(
        "bv",
        ["kn12"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/bv",
        None,
        is_commentary=False,
    ),
    "cp": SuttaCentralSource(
        "cp",
        ["kn13"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/cp",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/cp",
        is_commentary=False,
    ),
    "ja-1": SuttaCentralSource(
        "ja-1",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
        is_commentary=False,
        story_range=range(1, 351),
    ),
    "ja-2": SuttaCentralSource(
        "ja-2",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
        is_commentary=False,
        story_range=range(351, 455),
    ),
    "ja-3": SuttaCentralSource(
        "ja-3",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
        is_commentary=False,
        story_range=range(455, 497),
    ),
    "ja-4": SuttaCentralSource(
        "ja-4",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
        is_commentary=False,
        story_range=range(497, 511),
    ),
    "ja-5": SuttaCentralSource(
        "ja-5",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
        is_commentary=False,
        story_range=range(511, 548),
    ),
    "mnd": SuttaCentralSource(
        "mnd",
        ["kn15"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/mnd",
        None,
        is_commentary=False,
    ),
    "cnd": SuttaCentralSource(
        "cnd",
        ["kn16"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/cnd",
        None,
        is_commentary=False,
    ),
    "ps": SuttaCentralSource(
        "ps",
        ["kn17"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ps",
        None,
        is_commentary=False,
    ),
    "mil": SuttaCentralSource(
        "mil",
        ["kn18"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/mil",
        "resources/sc-data/sc_bilara_data/translation/en/kelly/sutta/kn/mil",
        is_commentary=False,
    ),
    "ne": SuttaCentralSource(
        "ne",
        ["kn19"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ne",
        None,
        is_commentary=False,
    ),
    "pe": SuttaCentralSource(
        "pe",
        ["kn20"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/pe",
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
    "dna": SuttaCentralSource(
        "dna",
        ["dna"],
        None,
        None,
        is_commentary=True,
    ),
    "mna": SuttaCentralSource(
        "mna",
        ["mna"],
        None,
        None,
        is_commentary=True,
    ),
    "sna": SuttaCentralSource(
        "sna",
        ["sna"],
        None,
        None,
        is_commentary=True,
    ),
    "ana": SuttaCentralSource(
        "ana",
        ["ana"],
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
}
