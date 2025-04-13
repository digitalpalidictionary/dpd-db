import re
from collections import defaultdict
from dataclasses import dataclass
from json import dump, load, loads
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
import random


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


class DatabaseManager:
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
                                related_entry = f"lemma_1: {headword.lemma_1}, pos: {headword.pos}, grammar: {headword.grammar}, meaning_1: {headword.meaning_combo}, root_key: {headword.root_key}, root_sign: {headword.root_sign}, root_base: {headword.root_base}, family_root: {headword.family_root}, family_compound: {headword.family_compound}, construction: {headword.construction}, stem: {headword.stem}, pattern: {headword.pattern}"
                                if related_entry not in related_entries_list:
                                    related_entries_list.append(related_entry)

        return related_entries_list


class Pass1PreProcessor:
    def __init__(self) -> None:
        self.books: dict[str, BookSource] = books
        self.db: DatabaseManager = DatabaseManager()
        self.pass1_dict: dict[str, list[Segment]] = {}
        self.book: str
        self.key: str
        self.values: list[Segment]
        self.related_entries_list: list[str] = []

        self.prompt: str
        self.response: str

        self.preprocessed_path = Path("gui2/pass1/preprocessed.json")
        self.preprocessed_dict: dict[str, dict[str, str]]
        self.preprocessed_keys: list[str]
        self.load_preprocessed()

    def load_preprocessed(self):
        if self.preprocessed_path.exists():
            self.preprocessed_dict = load(
                self.preprocessed_path.open("r", encoding="utf-8")
            )
            self.preprocessed_keys = list(self.preprocessed_dict.keys())

        else:
            self.preprocessed_dict = {}

    def update_preprocessed(self):
        # convert to json
        self.response = self.response.replace("```json", "").replace("```", "")
        self.preprocessed_dict[self.key] = loads(self.response)

        # add an example and translation
        self.preprocessed_dict[self.key]["example_1"] = self.values[0].pali
        self.preprocessed_dict[self.key]["translation_1"] = self.values[0].english

        # add a second example and translation
        if len(self.values) > 1:
            self.preprocessed_dict[self.key]["example_2"] = self.values[1].pali
            self.preprocessed_dict[self.key]["translation_2"] = self.values[1].english

        with self.preprocessed_path.open("w") as f:
            dump(self.preprocessed_dict, f, indent=2, ensure_ascii=False)

    def pre_process_book(self, book: str):
        self.book = book
        self.find_missing_words()
        for self.key, self.values in self.pass1_dict.items():
            print(self.key)
            self.related_entries_list = self.db.get_related_dict_entries(self.key)
            if self.related_entries_list:
                self.compile_prompt()
                self.response = str(self.send_prompt())
                self.update_preprocessed()

    def find_missing_words(self) -> None:
        for word, segments in self.books[self.book].word_dict.items():
            if (
                word not in self.db.all_inflections
                and word not in self.db.sandhi_ok_list
                and word not in self.preprocessed_keys
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

        self.prompt = f"""
## Word in the text
{self.key}

## Sentences: 
{"\n".join([f"{count}. Pāḷi : {v.pali}\n{count}. English: {v.english}\n" for count, v in enumerate(self.values)])}

## Related dictionary entries:
{"\n".join([f"- {entry}" for entry in self.related_entries_list])}
---        
You are an expert in Pāḷi grammar.
Based on the information above, please provide your very best suggestion of the word's:

1. lemma_1
2. pos
3. grammar
4. meaning_1
5. root_key
6. root_sign
7. root_base
8. family_root
9. family_compound
10. construction
11. stem
12. pattern
13. comments

## lemma_1 field
- This must be word in the text, without case endings. 
- Inflected verbs must be in 3rd singular, e.g. gacchanti = gacchati
- Declined nouns, adjectives and participles in vocative singular, e.g. narena = nara
- Sandhi compounds should be left example as they are, and pos marked as sandhi e.g. chahaṅgehi

## grammar field
- If the word is a compound, include part of speech, comma, comp e.g. dhammavinaya = masc, comp
- If the word is a noun derived from a root, show the word it is derived from e.g. vinaya = masc, from vineti
- If the word is a verbal form display it like this: avitaranta = prp of na vitarati
- if the word is a sandhi compound, grammar is sandhi and parts of speech, e.g. sandhi, masc + pron

## meaning_1 field
- Compare the Pāḷi sentence with the English sentence to understand how the word is being used in context. If possible provide multiple meanings, separated by semicolons. e.g. nara = man; person; human being
- In vinaya, words ending in vatthu mean 'case of ...'

## construction field
- Construction must be pure Pāḷi construction, no English. e.g. anupassati = anu + passa + ti, māra = √mar > mār + *a

## root_key, root_sign, root_base, family_root
- These fields only apply to words with a root, not to compounds. 
- Unless the word is derived from a root, leave them empty. 

## family root field
- The family_root is all the verbal prefixes and the root separated by spaces, e.g. samūhantabba = saṃ ud √han, anukamma = anu √kar

## family_compound
- The field only applies to words that are compounds. 
- Items are space separated, no plus signs +
- Taddhita should be reduced to kita, e.g. pannarasaka = pannarasa
- Negatives should just show the positive components, e.g. nadhammagaruka = dhamma garu 
- Inflected forms should be vocative sg, e.g. mūlāya = mūla 

## all other fields
- Analyse the related dictionary entries below and use the same style and pattern. Only add the required data, no commentary.

## comments
- Add your own commentary to this field, not to any other field.
- Only mention anything relevant or interesting, nothing that is already in other fields. 
- Explain the meaning according to the contextual sentence. 

## Return
- Return your results as a pure JSON, without any preceding or following text. Pure JSON only. 
---

"""

    def send_prompt(self):
        ds = Deepseek()
        try:
            return ds.request(
                model="deepseek-chat",
                prompt=self.prompt,
                prompt_sys="What an amazing Pāḷi grammar expert!",
            )
        except Exception as e:
            return e


def main() -> None:
    pre_process: Pass1PreProcessor = Pass1PreProcessor()
    pre_process.pre_process_book("vin3")


if __name__ == "__main__":
    main()
