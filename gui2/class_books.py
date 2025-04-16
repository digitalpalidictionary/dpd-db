from collections import defaultdict
from dataclasses import dataclass
from json import load
from pathlib import Path
from tools.clean_machine import clean_machine
from tools.pali_alphabet import pali_alphabet
from tools.sort_naturally import natural_sort


@dataclass
class Segment:
    segment: str
    pali: str
    english: str


class BookSource:
    def __init__(self, book: str, pali_path: str, english_path: str) -> None:
        self.book: str = book
        self.pali_path: Path = Path(pali_path)
        self.english_path: Path = Path(english_path)

        self.pali_file_list: list[Path] = self.make_file_list(self.pali_path)
        self.english_file_list: list[Path] = self.make_file_list(self.english_path)

        self.segment_dict: dict[str, Segment] = {}
        self.make_segment_dict()

        self.word_dict: defaultdict[str, list[Segment]] = defaultdict(list)
        self.allowable_chars: list[str] = pali_alphabet + [" "]
        self.process_words()

        # print(self.word_dict["virāgo"])

    def make_file_list(self, folder: Path) -> list[Path]:
        return natural_sort([f for f in folder.iterdir() if f.is_file()])

    def make_segment_dict(self) -> None:
        for file_path in self.pali_file_list:
            data: dict[str, str] = load(file_path.open("r", encoding="utf-8"))
            for segment, sentence in data.items():
                self.segment_dict[segment] = Segment(segment, sentence, "")

        for file_path in self.english_file_list:
            data: dict[str, str] = load(file_path.open("r", encoding="utf-8"))
            for segment, sentence in data.items():
                if segment in self.segment_dict:
                    self.segment_dict[segment].english = sentence
                else:
                    # sometimes only english exists
                    self.segment_dict[segment] = Segment(segment, "", sentence)

    def process_words(self) -> None:
        for segment in self.segment_dict.values():
            pali: str = clean_machine(segment.pali)
            for word in pali.split():
                self.word_dict[word].append(segment)


pass1_books: dict[str, BookSource] = {
    "vin3": BookSource(
        "vin3",
        "resources/sc-data/sc_bilara_data/root/pli/ms/vinaya/pli-tv-kd",
        "resources/sc-data/sc_bilara_data/translation/en/brahmali/vinaya/pli-tv-kd",
    ),
    "dn": BookSource(
        "dn",
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/dn",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/dn",
    ),
    "ja": BookSource(
        "ja",
        "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/ja",
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/ja",
    ),
}
