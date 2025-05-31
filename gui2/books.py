from collections import defaultdict, namedtuple
from json import load
from pathlib import Path

from tools.clean_machine import clean_machine
from tools.pali_alphabet import pali_alphabet
from tools.sort_naturally import natural_sort

SuttaCentralSegment = namedtuple("SuttaCentralSegment", ["segment", "pali", "english"])


class SuttaCentralSource:
    def __init__(
        self, book: str, cst_books: list[str], pali_path: str, english_path: str
    ) -> None:
        self.sc_book: str = book
        self.cst_books: list[str] = cst_books
        self.pali_path: Path = Path(pali_path)
        self.english_path: Path = Path(english_path)

        self.pali_file_list: list[Path] = self.make_file_list(self.pali_path)
        self.english_file_list: list[Path] = self.make_file_list(self.english_path)

        self.segment_dict: dict[str, SuttaCentralSegment] = {}
        self.make_segment_dict()

        self.word_dict: defaultdict[str, list[SuttaCentralSegment]] = defaultdict(list)
        self.allowable_chars: list[str] = pali_alphabet + [" "]
        self.process_words()

        # print(self.word_dict["virāgo"])

    def make_file_list(self, folder: Path) -> list[Path]:
        return natural_sort([f for f in folder.iterdir() if f.is_file()])

    def make_segment_dict(self) -> None:
        for file_path in self.pali_file_list:
            data: dict[str, str] = load(file_path.open("r", encoding="utf-8"))
            for segment, sentence in data.items():
                sentence = sentence.replace("ṁ", "ṃ").lower()
                self.segment_dict[segment] = SuttaCentralSegment(segment, sentence, "")

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
    "dn": SuttaCentralSource(
        "dn",
        ["dn3", "dn1", "dn2"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/dn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/dn",
    ),
    "ja": SuttaCentralSource(
        "ja",
        ["kn14"],
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
    ),
}
