import ast
import json
from pathlib import Path
from typing import Any, Iterator, Optional

from db.models import DpdHeadword
from gui2.books import SuttaCentralSource, sutta_central_books
from gui2.database_manager import DatabaseManager
from gui2.pass2_file_manager import Pass2AutoFileManager
from gui2.paths import Gui2Paths
from gui2.pass2_pre_controller import Pass2PreFileManager
from tools.deepseek import Deepseek
from tools.printer import printer as pr

debug = False


class Pass2AutoController:
    """
    Controller to process items marked 'yes' in Pass 2 Pre,
    query the database, interact with an AI, and save results.
    """

    def __init__(
        self,
        ui,
        db_manager: DatabaseManager,
    ) -> None:
        from gui2.pass2_auto_view import Pass2AutoView

        # globals
        self.db: DatabaseManager = db_manager
        self.ui: Pass2AutoView = ui

        # paths
        self._gui2pth = Gui2Paths()
        self._output_file: Path = self._gui2pth.pass2_auto_json_path
        self._failures_path: Path = self._gui2pth.pass2_auto_failures_path

        self._sc_books: dict[str, SuttaCentralSource] = sutta_central_books
        self.sc_books_list = [k for k in self._sc_books]

        self._book: str
        self._cst_books: list[str]

        self._pass2_pre_file_manager: Pass2PreFileManager
        self._pass2_auto_file_manager: Pass2AutoFileManager = Pass2AutoFileManager()
        self._pass2_matched_len: int

        self._results: dict[str, Any] = {}
        self._gui2pth = Gui2Paths()
        self._output_file: Path
        self._failures_path: Path
        self._yes_iter: Optional[Iterator[str]] = None
        self._fields: list[str] = [
            "id",
            "lemma_1",
            "lemma_2",
            "pos",
            "grammar",
            "derived_from",
            "neg",
            "verb",
            "trans",
            "plus_case",
            "meaning_1",
            "meaning_lit",
            "non_ia",
            "sanskrit",
            "root_key",
            "root_sign",
            "root_base",
            "family_root",
            "family_word",
            "family_compound",
            "family_idioms",
            "family_set",
            "construction",
            "derivative",
            "suffix",
            "phonetic",
            "compound_type",
            "compound_construction",
            "stem",
            "pattern",
        ]

        # single word — reset on every loop
        self.processed_count: int = 0
        self._word_in_text: str
        self._sentence_data: dict
        self._id: int
        self._headword: DpdHeadword
        self._related_words: list[DpdHeadword] | None
        self._prompt: str
        self._response_dict: dict[str, str] | None

        # flag
        self.stop_flag: bool = False

    def auto_process_book(self, book: str) -> None:
        """Process all items marked 'yes' in Pass 2 Pre."""

        self._book = book
        self._cst_books = self._sc_books[self._book].cst_books
        self._pass2_pre_file_manager = Pass2PreFileManager(self._book)
        self._pass2_matched_len: int = len(self._pass2_pre_file_manager.matched)

        try:
            if not self._pass2_pre_file_manager.matched:
                pr.red("No 'matched' items found")
                return

            matched_items = list(
                self._pass2_pre_file_manager.matched.items()
            )  # Create a list copy of items to avoid modification during iteration

            self.ui.update_auto_processed_count(
                f"{self.processed_count} / {self._pass2_matched_len}"
            )

            for self._word_in_text, self._sentence_data in matched_items:
                if self.stop_flag:
                    break

                if self._word_in_text not in self._pass2_pre_file_manager.processed:
                    self._process_single_item()

            if self.stop_flag:
                self.stop_flag = False
                self.processed_count = 0
                self.ui.clear_all_fields()
            else:
                self.processed_count = 0
                self.ui.clear_all_fields()
                self.ui.update_message("All items processed")

        except Exception as e:
            pr.red(f"Error during processing: {e}")

    def _process_single_item(self) -> bool:
        """Process a single item with all required steps"""

        self.ui.update_message(f"processing: {self._word_in_text}")

        try:
            self._id = self._sentence_data["id"]
            headword_in_db = self.db.get_headword_by_id(self._id)

            if not headword_in_db:
                pr.red(f"headword with id {self._id} not found in db")
                return False
            self._headword = headword_in_db

            # FIXME Improve to be more specific, then more general when necessary.
            self._related_words = self.db.get_related_headwords(self._headword)

            self._make_prompt()
            response = self._send_prompt()
            self._response_dict = self._format_response(response)

            if self._response_dict:
                self._add_sentence_to_response()

                self._pass2_auto_file_manager.update_response(
                    str(self._headword.id),
                    self._response_dict,
                )
                message = self._pass2_pre_file_manager.move_matched_item_to_processed(
                    self._word_in_text
                )
                self.ui.update_message(message)

                self.processed_count += 1
                self.ui.update_auto_processed_count(
                    f"{self.processed_count} / {self._pass2_matched_len}"
                )
                self.ui.update_word_in_text(self._word_in_text)
                self.ui.update_ai_results(
                    json.dumps(self._response_dict, indent=4, ensure_ascii=False)
                )

                if debug:
                    temp_file = Path(
                        f"temp/prompts/pass2/{self._word_in_text}_response"
                    )
                    with open(temp_file, "w") as f:
                        f.write(str(self._response_dict))

                return True

            else:
                return False

        except Exception as e:
            print(f"Error processing {self._word_in_text}: {e}")
            return False

    def _add_sentence_to_response(self):
        if self._response_dict:
            self._response_dict["source_1"] = self._sentence_data["sentence"][0]
            self._response_dict["sutta_1"] = self._sentence_data["sentence"][1]
            self._response_dict["example_1"] = self._sentence_data["sentence"][2]

    def _make_dict_string(self, headword: DpdHeadword) -> str:
        """Automatically convert DpdHeadword to Python dict string using all fields."""

        field_list = []
        for field in self._fields:
            value = getattr(headword, field)
            field_list.append(f"    '{field}': {repr(value)}")

        return "{\n" + ",\n".join(field_list) + "\n}"

    def _make_related_word_string(self) -> str:
        """Format related words list into Python dict string representation."""

        if not self._related_words:
            return "None"

        string_list = []
        for headword in self._related_words:
            string_list.append(self._make_dict_string(headword))

        return "[\n" + ",\n  ".join(string_list) + "\n]"

    def _make_sentence_string(self) -> str:
        string_list = []
        for i in self._sentence_data["sentence"]:
            string_list.append(i)

        return "\n".join(string_list) + "\n"

    def _make_prompt(self):
        """Make a prompt containing all headword data and
        data of related words."""

        self._prompt = f"""
# Digital Pāḷi Dictionary Entry

You are an expert in Pāḷi grammar.

Please complete ALL fields below EXACTLY as shown, filling missing data and correcting errors.

PRESERVE the original formatting, field order, and structure.

Add any comments you wish to add to a COMMENTS field at the end of the data.

Return ONLY the Python dictionary portion, starting and ending with curly braces, with no additional text or explanations.

---

## Headword

{self._headword.lemma_1}

{self._make_dict_string(self._headword)}

## Contextual Sentence

{self._make_sentence_string()}

## Related headwords

{self._make_related_word_string()}

---

# Grammatical Field Reference 

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

## family_root field
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

## All other fields
- Analyse the related dictionary entries above and use the same style and pattern. Only add the required data, no commentary.

## Comments
- Add your own commentary to this field, not to any other field.
- Only mention anything relevant or interesting, nothing that is already in other fields. 
- Explain the meaning according to the contextual sentence. 

## Return
- Return your results as a pure string which can be directly imported into Python as a dict.
---


"""
        if debug:
            temp_file = Path(f"temp/prompts/pass2/{self._word_in_text}_prompt")
            with open(temp_file, "w") as f:
                f.write(self._prompt)

    def _send_prompt(self):
        ds = Deepseek()
        try:
            response = str(
                ds.request(
                    model="deepseek-chat",
                    prompt=self._prompt,
                    prompt_sys="Follow the instructions very carefully.",
                )
            )
            # Extract just the dictionary portion
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return response[start:end]
            return response  # fallback if no dict found
        except Exception as e:
            return str(e)

    def _format_response(self, response: str) -> dict[str, str] | None:
        """Format the response into a valid python dict
        or save it to the failures file for manual editing."""

        result = None

        try:
            result = ast.literal_eval(response)
        except (SyntaxError, ValueError):
            try:
                json_str = response.replace("'", '"')
                result = json.loads(json_str)
            except json.JSONDecodeError:
                pass

        if result is None:
            pr.red("adding response to failures")
            with open(self._failures_path, "a", encoding="utf-8") as f:
                f.write(response + "\n\n")

        return result
