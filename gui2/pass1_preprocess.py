from collections import defaultdict
from dataclasses import dataclass
from json import dump, dumps, load, loads
from pathlib import Path
import subprocess

from rich import print

import db.inflections.generate_inflection_tables
from tools.clean_machine import clean_machine
from tools.goldendict_tools import open_in_goldendict_os
from tools.pali_alphabet import pali_alphabet
from tools.sort_naturally import natural_sort
from tools.deepseek import Deepseek
from gui2.database import DatabaseManager


import flet as ft


class Pass1PreProcessView(ft.Column):
    def __init__(self, page: ft.Page) -> None:
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )
        self.page: ft.Page = page
        self.controller = Pass1PreProcessController(self)

        # Define constants
        LABEL_WIDTH: int = 150
        COLUMN_WIDTH: int = 700

        # Define controls
        self.message_field = ft.Text(
            "",
            expand=True,
            color=ft.Colors.BLUE_200,
        )
        self.book_field = ft.TextField(
            "",
            width=300,
            autofocus=True,
            on_submit=self.handle_book_click,
        )
        self.preprocessed_count_field = ft.TextField(
            "",
            expand=True,
        )
        self.word_in_text_field = ft.TextField(
            "",
            width=COLUMN_WIDTH,
            expand=True,
        )
        self.ai_results_field = ft.TextField(
            "",
            width=COLUMN_WIDTH,
            multiline=True,
            expand=True,
        )

        self.controls.extend(
            [
                ft.Row(
                    controls=[
                        ft.Text("", width=LABEL_WIDTH),
                        self.message_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("book", width=LABEL_WIDTH),
                        self.book_field,
                        ft.ElevatedButton(
                            "PreProcess Book",
                            on_click=self.handle_book_click,
                        ),
                        ft.ElevatedButton(
                            "Stop",
                            on_click=self.handle_stop_click,
                        ),
                        ft.ElevatedButton(
                            "Clear",
                            on_click=self.handle_clear_click,
                        ),
                        ft.ElevatedButton(
                            "Update inflections",
                            on_click=self.handle_update_inflections_click,
                        ),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("preprocessed", width=LABEL_WIDTH),
                        self.preprocessed_count_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("word in text", width=LABEL_WIDTH),
                        self.word_in_text_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("ai results", width=LABEL_WIDTH),
                        self.ai_results_field,
                    ]
                ),
            ]
        )

    def handle_book_click(self, e):
        if self.book_field.value:
            self.controller.preprocess_book(self.book_field.value)

    def handle_stop_click(self, e):
        self.controller.stop_flag = True

    def handle_clear_click(self, e):
        self.clear_all_fields()

    def handle_update_inflections_click(self, e):
        self.update_message("updating inflections...")
        db.inflections.generate_inflection_tables.main()
        self.update_message("inflections updated")

    def update_message(self, message: str):
        self.message_field.value = message
        self.page.update()

    def update_ai_results(self, results: str):
        self.ai_results_field.value = results
        self.page.update()

    def update_word_in_text(self, word: str):
        self.word_in_text_field.value = word
        self.page.update()

    def update_preprocessed_count(self, count: int):
        self.preprocessed_count_field.value = str(count)
        self.page.update()

    def clear_all_fields(self):
        self.message_field.value = ""
        self.preprocessed_count_field.value = ""
        self.book_field.value = ""
        self.ai_results_field.value = ""
        self.word_in_text_field.value = ""
        self.page.update()


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


class Pass1PreProcessController:
    def __init__(self, ui: Pass1PreProcessView) -> None:
        self.ui: Pass1PreProcessView = ui
        self.pass1_books: dict[str, BookSource] = pass1_books
        self.db: DatabaseManager = DatabaseManager()
        self.pass1_dict: dict[str, list[Segment]] = {}
        self.book: str
        self.word_in_text: str
        self.sentence_data: list[Segment]
        self.related_entries_list: list[str] = []

        self.stop_flag = False

        self.prompt: str
        self.response: str

        self.preprocessed_dict: dict[str, dict[str, str]] = {}
        self.preprocessed_keys: list[str] = []

    def load_preprocessed(self):
        self.ui.update_message(f"Loading preprocessed data for {self.book}")

        self.preprocessed_path: Path = Path(f"gui2/data/{self.book}_preprocessed.json")
        if self.preprocessed_path.exists():
            self.preprocessed_dict = load(
                self.preprocessed_path.open("r", encoding="utf-8")
            )
            self.preprocessed_keys = list(self.preprocessed_dict.keys())

        else:
            self.preprocessed_dict = {}

        self.ui.update_preprocessed_count(len(self.preprocessed_dict))

    def preprocess_book(self, book: str):
        # should only run once
        if not self.db.all_inflections:
            self.ui.update_message("Loading database...")
            self.db.make_inflections_lists()

        self.book = book
        self.load_preprocessed()
        self.find_missing_words()
        for self.word_in_text, self.sentence_data in self.pass1_dict.items():
            self.ui.update_message(f"Processing {self.word_in_text}")

            self.related_entries_list = self.db.get_related_dict_entries(
                self.word_in_text
            )
            if self.related_entries_list:
                self.compile_prompt()
                self.response = str(self.send_prompt())
                self.update_preprocessed()
            if self.stop_flag:
                break

        self.ui.clear_all_fields()

    def find_missing_words(self) -> None:
        self.ui.update_message(f"Finding missing words for {self.book}")

        for word, segments in self.pass1_books[self.book].word_dict.items():
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

        self.ui.update_message(f"compiling prompt for {self.word_in_text}")

        self.prompt = f"""
## Word in the text
{self.word_in_text}

## Sentences: 
{"\n".join([f"{count}. Pāḷi : {v.pali}\n{count}. English: {v.english}\n" for count, v in enumerate(self.sentence_data)])}

## Related dictionary entries:
{"\n".join([f"- {entry}" for entry in self.related_entries_list])}
---        
You are an expert in Pāḷi grammar.
Based on the information above, please provide your very best suggestion of the word's:

1. lemma_1
2. lemma_1
3. pos
4. grammar
5. meaning_2
6. root_key
7. root_sign
8. root_base
9. family_root
10. family_compound
11. construction
12. stem
13. pattern
14. comments

## lemma_1 field
- This must be word in the text, without case endings. 
- Inflected verbs must be in 3rd singular, e.g. gacchanti = `gacchati`
- Declined nouns, adjectives and participles in vocative singular, e.g. narena = `nara`
- Sandhi compounds should be left example as they are, and pos marked as sandhi e.g. `chahaṅgehi`

## pos field
- For adverbs, and all indecliables, the pos is `ind`. The grammar is `ind, adv`.

## lemma_2 field
- For verbs, participles, adjectives, adverbs, etc. it is the same as lemma_1
- For nouns, it is the nominitve singular, e.g. buddha = `buddho`

## grammar field
- If the word is a compound, include part of speech, comma, comp e.g. dhammavinaya = `masc, comp`
- If the word is a noun derived from a root, show the word it is derived from e.g. vinaya = `masc, from vineti`
- If the word is a verbal form display it like this: avitaranta = `prp of na vitarati`
- if the word is a sandhi compound, grammar is sandhi and parts of speech, e.g. `sandhi, masc + pron`

## meaning_2 field
- Compare the Pāḷi sentence with the English sentence to understand how the word is being used in context. If possible provide multiple meanings, separated by semicolons. e.g. nara = man; person; human being
- In vinaya, words ending in vatthu mean 'case of ...'

## construction field
- Construction must be pure Pāḷi construction, no English. e.g. anupassati = `anu + passa + ti`, māra = `√mar > mār + *a`

## root_key, root_sign, root_base, family_root
- These fields only apply to words with a root, not to compounds. 
- Unless the word is derived from a root, leave them empty. 

## family root field
- The family_root is all the verbal prefixes and the root separated by spaces, e.g. samūhantabba = saṃ ud √han, anukamma = anu √kar

## family_compound
- The field only applies to words that are compounds. 
- Items are space separated, no plus signs +
- Taddhita should be reduced to kita, e.g. pannarasaka = `pannarasa`
- Negatives should just show the positive components, e.g. nadhammagaruka = `dhamma garu`
- Inflected forms should be vocative sg, e.g. mūlāya = `mūla`

## stem and pattern
- For sandhi stem is `-`, pattern is empty
- For all indeclinables, infinitives, absolutes adverbs, stem is `-`, pattern is empty
- Carefully analyse the provided stems and patterns, and don't make anything up.

## all other fields
- Analyse the related dictionary entries above and use the same style and pattern. Only add the required data, no commentary.

## comments
- Add your own commentary to this field, not to any other field.
- Only mention anything relevant or interesting, nothing that is already in other fields. 
- Explain the meaning according to the contextual sentence. 

## Return
- Return your results as a pure JSON, without any preceding or following text. Pure JSON only. 
---

"""

    def send_prompt(self):
        self.ui.update_message(f"sending prompt for {self.word_in_text}")

        ds = Deepseek()
        try:
            return ds.request(
                model="deepseek-chat",
                prompt=self.prompt,
                prompt_sys="What an amazing Pāḷi grammar expert!",
            )
        except Exception as e:
            return e

    def update_preprocessed(self):
        self.ui.update_message(f"updating preprocessed data for {self.word_in_text}")

        # convert to json
        self.response = self.response.replace("```json\n", "").replace("```", "")

        # update preprocessed_dict
        try:
            self.preprocessed_dict[self.word_in_text] = loads(self.response)

            # add an example and translation
            first_sentence = self.sentence_data[0]
            self.preprocessed_dict[self.word_in_text]["example_1"] = first_sentence.pali
            self.preprocessed_dict[self.word_in_text]["translation_1"] = (
                first_sentence.english
            )

            # add a second example and translation if it exists
            if len(self.sentence_data) > 1:
                second_sentence = self.sentence_data[1]
                self.preprocessed_dict[self.word_in_text]["example_2"] = (
                    second_sentence.pali
                )
                self.preprocessed_dict[self.word_in_text]["translation_2"] = (
                    second_sentence.english
                )

            # update gui
            open_in_goldendict_os(self.word_in_text)
            self.ui.update_word_in_text(self.word_in_text)
            self.ui.update_preprocessed_count(len(self.preprocessed_dict))
            self.ui.update_ai_results(
                dumps(
                    self.preprocessed_dict[self.word_in_text],
                    indent=2,
                    ensure_ascii=False,
                    separators=("", ":"),
                )
            )

            # save json
            with self.preprocessed_path.open("w") as f:
                dump(self.preprocessed_dict, f, indent=2, ensure_ascii=False)

        except Exception:
            self.ui.update_message("Error parsing JSON.")
