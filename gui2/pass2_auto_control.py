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
from tools.ai_manager import AIManager
from tools.goldendict_tools import open_in_goldendict_os
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
        ai_manager: AIManager,
    ) -> None:
        from gui2.pass2_auto_view import Pass2AutoView

        # globals
        self.ui: Pass2AutoView = ui
        self.db: DatabaseManager = db_manager
        self.ai_manager = ai_manager

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
        self._sentence_data_batch: dict
        self._id: int

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
                self.ui.update_message("No 'matched' items found. Run Pass2Pre.")
                return

            matched_items = list(
                self._pass2_pre_file_manager.matched.items()
            )  # Create a list copy of items to avoid modification during iteration

            self.ui.update_auto_processed_count(
                f"{self.processed_count} / {self._pass2_matched_len}"
            )

            for self._word_in_text, self._sentence_data_batch in matched_items:
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

    def _process_single_item(self) -> None:
        """
        Fetches data for a single item from the batch list (_pass2_pre_file_manager.matched)
        and orchestrates its processing using the core AI function. Handles file management
        and UI updates specific to batch mode.
        """

        self.ui.update_message(f"processing: {self._word_in_text}")

        try:
            self._id = self._sentence_data_batch["id"]
            headword_in_db = self.db.get_headword_by_id(self._id)

            if not headword_in_db:
                pr.red(f"headword with id {self._id} not found in db")
                # Optionally move to failures or skip
                return

            # Call the core AI processing function
            response_dict = self._process_headword_with_ai(
                headword_in_db, self._sentence_data_batch
            )

            if response_dict:
                # Update the main auto file
                self._pass2_auto_file_manager.update_response(
                    str(headword_in_db.id),
                    response_dict,
                )
                # Move item from matched to processed in the pre-processing file
                message = self._pass2_pre_file_manager.move_matched_item_to_processed(
                    self._word_in_text
                )
                self.ui.update_message(message)

                # Update batch UI
                self.processed_count += 1
                self.ui.update_auto_processed_count(
                    f"{self.processed_count} / {self._pass2_matched_len}"
                )
                self.ui.update_word_in_text(self._word_in_text)
                self.ui.update_ai_results(
                    json.dumps(response_dict, indent=4, ensure_ascii=False)
                )
                open_in_goldendict_os(self._word_in_text)  # Keep GD lookup for batch

                if debug:
                    temp_file = Path(
                        f"temp/prompts/pass2/{self._word_in_text}_response"
                    )
                    with open(temp_file, "w") as f:
                        f.write(str(response_dict))
            # else: Error handled within _process_headword_with_ai or _format_response

        except Exception as e:
            pr.red(f"Error processing {self._word_in_text}: {e}")
            # Optionally log failure

    # --- Core AI Processing Function ---
    def _process_headword_with_ai(
        self, headword: DpdHeadword, sentence_data: Optional[dict] = None
    ) -> Optional[dict[str, str]]:
        """
        Core function to process a single DpdHeadword using AI.
        Fetches related words, creates prompt, sends to AI, formats response.

        Args:
            headword: The DpdHeadword object to process.
            sentence_data: Optional dictionary containing sentence context
                           (expected format: {"sentence": [source, sutta, example]}).

        Returns:
            A dictionary with the AI's suggestions, or None if an error occurred.
        """
        try:
            related_words = self.db.get_related_headwords(headword)
            prompt = self._make_prompt(headword, related_words, sentence_data)
            raw_response = self._send_prompt(prompt)
            response_dict = self._format_response(raw_response)

            if response_dict and sentence_data:
                self._add_sentence_to_response(response_dict, sentence_data)

            return response_dict

        except Exception as e:
            pr.red(f"Error in _process_headword_with_ai for {headword.lemma_1}: {e}")
            return None

    # --- Helper Functions (Modified for Parameterization) ---

    def _add_sentence_to_response(self, response_dict: dict, sentence_data: dict):
        """Adds sentence data to the response dictionary if available."""
        if (
            response_dict
            and sentence_data
            and "sentence" in sentence_data
            and len(sentence_data["sentence"]) == 3
        ):
            response_dict["source_1"] = sentence_data["sentence"][0]
            response_dict["sutta_1"] = sentence_data["sentence"][1]
            response_dict["example_1"] = sentence_data["sentence"][2]

    def _make_dict_string(self, headword: DpdHeadword) -> str:
        """Automatically convert DpdHeadword to Python dict string using all fields."""

        field_list = []
        for field in self._fields:  # Corrected access to self._fields
            value = getattr(headword, field)
            field_list.append(f"    '{field}': {repr(value)}")

        return "{\n" + ",\n".join(field_list) + "\n}"

    def _make_related_word_string(
        self, related_words: Optional[list[DpdHeadword]]
    ) -> str:
        """Format related words list into Python dict string representation."""

        if not related_words:
            return "None"

        string_list = []
        for headword in related_words:
            string_list.append(self._make_dict_string(headword))

        return "[\n" + ",\n  ".join(string_list) + "\n]"

    def _make_sentence_string(self, sentence_data: Optional[dict]) -> str:
        """Creates a string representation of the sentence context."""
        if (
            not sentence_data
            or "sentence" not in sentence_data
            or not sentence_data["sentence"]
        ):
            return "No contextual sentence provided.\n"

        string_list = []
        for i in sentence_data["sentence"]:
            string_list.append(i)

        return "\n".join(string_list) + "\n"

    def _make_prompt(
        self,
        headword: DpdHeadword,
        related_words: Optional[list[DpdHeadword]],
        sentence_data: Optional[dict],
    ) -> str:
        """Make a prompt containing all headword data and
        data of related words."""

        prompt = f"""
# Digital Pāḷi Dictionary Entry

You are an expert in Pāḷi grammar.

Please complete ALL fields below EXACTLY as shown, filling missing data and correcting errors.

PRESERVE the original formatting, field order, and structure.

Add any comments you wish to add to a `comments` field at the end of the data.

Return ONLY the Python dictionary portion, starting and ending with curly braces, with no additional text or explanations.

---

## Headword

{headword.lemma_1}

{self._make_dict_string(headword)}

## Contextual Sentence

{self._make_sentence_string(sentence_data)}

## Related headwords

{self._make_related_word_string(related_words)} # Pass related_words explicitly

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
- Call the field 'comment'
- Only mention anything relevant or interesting, nothing that is already in other fields. 
- Explain the meaning according to the contextual sentence. 

## Return
- Return your results as a pure string which can be directly imported into Python as a dict.
---


"""
        if debug:
            temp_file = Path(f"temp/prompts/pass2/{headword.lemma_1}_prompt")
            with open(temp_file, "w") as f:
                f.write(prompt)
        return prompt

    def _send_prompt(self, prompt: str) -> str:
        try:
            response = str(
                self.ai_manager.request(
                    prompt=prompt,
                    prompt_sys="Follow the instructions very carefully.",
                )
            )
            # Extract just the dictionary portion
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return response[start:end].strip()  # Added strip()
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

    # --- Public Method for Single Word Update ---
    def process_single_headword_from_view(
        self,
        headword: DpdHeadword,
        # Consider how to get context if needed. For now, none.
        # sentence_data: Optional[dict] = None
    ) -> Optional[dict[str, str]]:
        """
        Processes a single DpdHeadword provided externally (e.g., from Pass2AddView).
        Calls the core AI function and returns the result.
        Does NOT handle file management or UI updates directly, that's the caller's responsibility.
        """
        pr.info(f"Processing single headword: {headword.lemma_1} (ID: {headword.id})")
        # Pass None for sentence_data, or derive it from headword.example_1 etc. if desired
        response_dict = self._process_headword_with_ai(headword, None)
        if response_dict:
            pr.info(f"AI processing successful for {headword.lemma_1}")
        return response_dict
