# -*- coding: utf-8 -*-
from json import JSONDecodeError, dump, dumps, load, loads
from pathlib import Path

from gui2.books import (
    SuttaCentralSegment,
    SuttaCentralSource,
    sutta_central_books,
)
from gui2.spelling import SpellingMistakesFileManager
from gui2.toolkit import ToolKit
from gui2.variants import VariantReadingFileManager
from tools.ai_manager import AIResponse
from tools.cst_sc_text_sets import make_cst_text_list
from tools.goldendict_tools import open_in_goldendict_os
from tools.printer import printer as pr


class Pass1AutoController:
    def __init__(
        self,
        ui,  # Pass1AutoView
        toolkit: ToolKit,
    ) -> None:
        from gui2.pass1_auto_view import Pass1AutoView

        self.ui: Pass1AutoView = ui
        self.db = toolkit.db_manager
        self.ai_manager = toolkit.ai_manager

        self.gui2pth = toolkit.paths
        self.pass1_books: dict[str, SuttaCentralSource] = sutta_central_books
        self.pass1_books_list = [k for k in self.pass1_books]

        self.missing_words_dict: dict[str, list[SuttaCentralSegment]] = {}
        self.book: str
        self.cst_books: list[str]
        self.all_cst_words: list[str] = []
        self.word_in_text: str
        self.sentence_data: list[SuttaCentralSegment]
        self.related_entries_list: list[str] = []

        self.stop_flag = False

        self.prompt: str
        self.response: str | None = None  # Can be None if AI request fails
        self.ai_status_message: str = ""  # To store status from AIManager

        self.auto_processed_dict: dict[str, dict[str, str]] = {}
        self.auto_processed_keys: list[str] = []

        self.variant_readings = VariantReadingFileManager()
        self.spelling_mistakes = SpellingMistakesFileManager()

    def load_auto_processed(self):
        self.ui.update_message(f"Loading auto processed data for {self.book}")

        self.auto_processed_path: Path = (
            self.gui2pth.gui2_data_path / f"pass1_auto_{self.book}.json"
        )
        if self.auto_processed_path.exists():
            self.auto_processed_dict = load(
                self.auto_processed_path.open("r", encoding="utf-8")
            )
            self.auto_processed_keys = list(self.auto_processed_dict.keys())

        else:
            self.auto_processed_dict = {}

        self.ui.update_auto_processed_count(
            f"{len(self.auto_processed_dict)} / {len(self.missing_words_dict)}"
        )

    def auto_process_book(self, book: str):
        self.stop_flag = False

        # should only run once.
        # actually no, should run clean every time to update changes in db
        # if not self.db.all_inflections:
        self.ui.update_message("Loading database...")
        self.db.make_inflections_lists()

        self.book = book
        self.cst_books = sutta_central_books[book].cst_books
        self.load_auto_processed()
        self.find_missing_words_in_cst()
        self.find_missing_words_in_sutta_central()
        for self.word_in_text, self.sentence_data in self.missing_words_dict.items():
            self.ui.update_message(f"Processing {self.word_in_text}")

            self.related_entries_list = self.db.get_related_dict_entries(
                self.word_in_text
            )
            self.compile_prompt()

            selected_model_str = self.ui.ai_model_dropdown.value
            provider_preference = None
            model_name = None
            if selected_model_str:
                parts = selected_model_str.split("|", 1)
                if len(parts) == 2:
                    provider_preference, model_name = parts

            ai_resp = self.send_prompt(
                provider_preference=provider_preference, model=model_name
            )
            self.response = ai_resp.content
            self.ai_status_message = ai_resp.status_message
            self.ui.update_message(ai_resp.status_message)
            if self.response is None:
                break

            elif not self.update_auto_processed(provider_preference, model_name):
                pass

            if self.stop_flag:
                self.ui.clear_all_fields()
                self.ui.update_message("stopped")
                break

        #

    def is_missing(self, word: str):
        if (
            word not in self.db.all_inflections
            and word not in self.db.sandhi_ok_list
            and word not in self.auto_processed_keys
            and word not in self.variant_readings.variants_dict
            and word not in self.spelling_mistakes.spelling_mistakes_dict
        ):
            return True
        else:
            return False

    def find_missing_words_in_cst(self) -> None:
        """Find all the missing words in CST."""

        self.ui.update_message("Finding missing words in CST")

        # just run once, it doesn't change
        # if not self.all_cst_words: actually needs to change for every book
        self.all_cst_words = make_cst_text_list(self.cst_books, dedupe=True)

        for word in self.all_cst_words:
            if self.is_missing(word):
                self.missing_words_dict[word] = []

    def find_missing_words_in_sutta_central(self) -> None:
        """Find all the missing words in SC and add their sentences."""

        self.ui.update_message("Finding missing words in Sutta Central")

        for word, segments in self.pass1_books[self.book].word_dict.items():
            if self.is_missing(word):
                self.missing_words_dict[word] = segments

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
2. lemma_2
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
14. comment

## lemma_1 field
- This must be word in the text, without case endings. 
- Inflected verbs must be in 3rd singular, e.g. gacchanti = `gacchati`
- Declined nouns, adjectives and participles in vocative singular, e.g. narena = `nara`
- Sandhi compounds should be left example as they are, and pos marked as sandhi e.g. `chahaṅgehi`

## lemma_2 field
- For verbs, participles, adjectives, adverbs, etc. it is the same as lemma_1
- For nouns, it is the nominitve singular, e.g. buddha = `buddho`


## pos field
- For adverbs, and all indecliables, the pos is `ind`. The grammar is `ind, adv`.
- In general, words ending in `ādi` are `masc`. 
- The only parts of speech to be added are these:
abbrev: abbreviation
abs: absolutive
adj: adjective
aor: aorist
card: cardinal number
cond: conditional verb
cs: conjugational sign
fem: feminine noun
fut: future verb
ger: gerund
idiom: idiomatic expression
imp: imperative verb
imperf: imperfect verb
ind: indeclinable
inf: infinitive
letter: letter of the alphabet
masc: masculine noun
nt: neuter noun
opt: optative verb
ordin: ordinal number
perf: perfect verb
pp: past participle
pr: present tense verb
prefix: prefix
pron: pronoun
prp: present participle
ptp: potential participle
root: root
sandhi: sandhi compound
suffix: suffix
ve: verbal ending

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

## comment
- Add your own commentary to this field, not to any other field.
- Only mention anything relevant or interesting, nothing that is already in other fields. 
- Explain the meaning according to the contextual sentence. 

## Return
- Return your results as a pure JSON, without any preceding or following text. Pure JSON only. 
---

"""
        temp_file = Path(f"temp/prompts/pass1/{self.word_in_text}_prompt")
        with open(temp_file, "w") as f:
            f.write(self.prompt)

    def send_prompt(
        self, provider_preference: str | None = None, model: str | None = None
    ) -> AIResponse:  # Changed return type
        self.ui.update_message(
            f"Sending prompt for {self.word_in_text} using {model or 'default model'}..."
        )

        try:
            ai_response = self.ai_manager.request(
                prompt=self.prompt,
                prompt_sys="Follow the instructions very carefully.",
                provider_preference=provider_preference,
                model=model,
            )
            return ai_response
        except Exception as e:
            return AIResponse(
                content=None,
                status_message=f"Exception during AI request for {self.word_in_text}: {e}",
            )

    def update_auto_processed(self, provider: str | None, model: str | None) -> bool:
        if not isinstance(self.response, str):
            self.ui.update_message(
                f"Error for {self.word_in_text}: AI response content is not a string ({type(self.response)}). Original AI Status: {self.ai_status_message}"
            )
            return False

        # Attempt to clean and parse the JSON response
        try:
            cleaned_response = self.response.replace("```json\n", "").replace("```", "")

            # Try parsing the cleaned response
            parsed_json = loads(cleaned_response)

            # add ai details
            if provider:
                try:
                    comment = parsed_json["comment"]
                    parsed_json["comment"] = f"[{provider}: {model}] {comment}"
                except KeyError:
                    pr.error("ERROR adding ai model to comment")

            # save json to temp file
            tempfile = Path(f"temp/prompts/pass1/{self.word_in_text}_response")
            with open(tempfile, "w") as f:
                dump(parsed_json, f, ensure_ascii=False, indent=4)

            # update auto processed_dict
            self.auto_processed_dict[self.word_in_text] = parsed_json

            # add examples and translations
            if len(self.sentence_data) > 0:
                first_sentence = self.sentence_data[0]
                self.auto_processed_dict[self.word_in_text]["example_1"] = (
                    first_sentence.pali
                )
                self.auto_processed_dict[self.word_in_text]["translation_1"] = (
                    first_sentence.english
                )

            if len(self.sentence_data) > 1:
                second_sentence = self.sentence_data[1]
                self.auto_processed_dict[self.word_in_text]["example_2"] = (
                    second_sentence.pali
                )
                self.auto_processed_dict[self.word_in_text]["translation_2"] = (
                    second_sentence.english
                )

            # update gui
            open_in_goldendict_os(self.word_in_text)
            self.ui.update_word_in_text(self.word_in_text)
            self.ui.update_auto_processed_count(
                f"{len(self.auto_processed_dict)} / {len(self.missing_words_dict)}"
            )
            self.ui.update_ai_results(
                dumps(
                    self.auto_processed_dict[self.word_in_text],
                    indent=4,
                    ensure_ascii=False,
                    separators=("", ":"),
                )
            )

            # save updated dictionary to main file
            with self.auto_processed_path.open("w") as f:
                dump(
                    self.auto_processed_dict,
                    f,
                    indent=4,
                    ensure_ascii=False,
                )

        except JSONDecodeError as e:
            # Handle the case where the response is not valid JSON
            error_message = f"Error processing '{self.word_in_text}': Failed to decode API response. Details: {e}. Original AI Status: {self.ai_status_message}"
            self.ui.update_message(error_message)
            return False

        except Exception as e:
            # Catch any other unexpected errors during processing
            error_message = f"Unexpected error processing '{self.word_in_text}': {e}. Original AI Status: {self.ai_status_message}"
            self.ui.update_message(error_message)
            return False

        return True
