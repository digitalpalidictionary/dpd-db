import re
from collections import defaultdict
from dataclasses import dataclass
from json import load
from pathlib import Path

from google import genai
from rich import print
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.clean_machine import clean_machine
from tools.configger import config_read
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sort_naturally import natural_sort
from tools.deepseek import Deepseek


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


books: dict[str, BookSource] = {
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
}


class DbManager:
    def __init__(self) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()

        self.all_inflections: set[str] = set()
        [self.all_inflections.update(i.inflections_list_all) for i in self.db]

        self.all_inflections_missing_meaning: set[str] = set()
        [
            self.all_inflections_missing_meaning.update(i.inflections_list_all)
            for i in self.db
            if not i.meaning_1
        ]

        self.sandhi_ok_list: list[str] = self.pth.decon_checked.read_text().splitlines()

    def get_related_dict_entries(self, word_in_text) -> list[str]:
        """Get all the possible lemma, pos meaning for a word."""

        related_entries_list: list[str] = []
        lookup_results: list[Lookup] = (
            self.db_session.query(Lookup)
            .filter(Lookup.lookup_key == word_in_text)
            .all()
        )
        for i in lookup_results:
            for deconstruction in i.deconstructor_unpack[:2]:  # limit results
                for word in deconstruction.split(" + "):
                    single_result = (
                        self.db_session.query(Lookup)
                        .filter(Lookup.lookup_key == word)
                        .first()
                    )
                    if single_result:
                        ids = single_result.headwords_unpack
                        for id in ids:
                            headword: DpdHeadword | None = (
                                self.db_session.query(DpdHeadword)
                                .filter(DpdHeadword.id == id)
                                .first()
                            )
                            if headword:
                                related_entry = f"{headword.lemma_1}. {headword.pos}. {headword.meaning_combo}"
                                if related_entry not in related_entries_list:
                                    related_entries_list.append(related_entry)

        return related_entries_list


class PreProcessor:
    def __init__(self) -> None:
        self.books: dict[str, BookSource] = books
        self.db: DbManager = DbManager()
        self.pass1_dict: dict[str, list[Segment]] = {}
        self.book: str
        self.key: str
        self.values: list[Segment]
        self.related_entries_list: list[str] = []

        # prompt related
        self.prompt: str
        # self.api_key = config_read("apis", "gemini")
        # self.client = genai.Client(api_key=self.api_key)
        # self.model = "gemini-2.0-flash"
        # self.model = "gemini-2.5-pro-exp-03-25"

    def find_missing_words(self) -> None:
        for word, segments in self.books[self.book].word_dict.items():
            if (
                word not in self.db.all_inflections
                and word not in self.db.sandhi_ok_list
            ):
                self.pass1_dict[word] = segments

    def compile_prompt(self):
        """
        Compile a text prompt of
        1. word
        2. pali sentences
        3. english sentences
        4. related dpd entries
        """

        self.prompt = f"""You are an expert in Pāḷi grammar.
Based on the information below, please provide your very best suggestion of the word's 
1. lemma
2. part of speech
2. meaning
3. construction 

Compare the Pāḷi sentence with the English sentence to understand how the word is being used in context. 
Analyse the related dictionary entries to understand the grammar of the word.

Return your results as a pure JSON, without any preceding or following text. Pure JSON only. 
---
## Word in the text
{self.key}

## Sentences: 
{"\n".join([f"{count}. Pāḷi : {v.pali}\n{count}. English: {v.english}\n" for count, v in enumerate(self.values)])}

## Related dictionary entries:
{"\n".join([f"- {entry}" for entry in self.related_entries_list])}
"""

    def send_prompt(self):
        ds = Deepseek()
        try:
            return ds.request(
                model="deepseek-reasoner",
                prompt=self.prompt,
                prompt_sys="What an amazing Pāḷi grammar expert!",
            )
        except Exception as e:
            return e

    def pre_process_book(self, book: str):
        self.book = book
        self.find_missing_words()
        for self.key, self.values in self.pass1_dict.items():
            self.related_entries_list = self.db.get_related_dict_entries(self.key)
            if self.related_entries_list:
                self.compile_prompt()
                response = self.send_prompt()
                print(response)
                input()


def main() -> None:
    pre_process: PreProcessor = PreProcessor()
    pre_process.pre_process_book("vin3")


if __name__ == "__main__":
    main()
