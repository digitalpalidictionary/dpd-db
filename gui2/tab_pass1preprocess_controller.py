from json import dump, dumps, load, loads
from pathlib import Path

from gui2.class_books import BookSource, Segment, pass1_books
from gui2.class_database import DatabaseManager
from tools.cst_sc_text_sets import make_cst_text_list
from tools.deepseek import Deepseek
from tools.goldendict_tools import open_in_goldendict_os


class Pass1PreProcessController:
    def __init__(self, ui, db: DatabaseManager) -> None:
        from gui2.tab_pass1preprocess_view import Pass1PreProcessView

        self.ui: Pass1PreProcessView = ui

        self.pass1_books: dict[str, BookSource] = pass1_books
        self.pass1_books_list = [k for k in self.pass1_books]

        self.db: DatabaseManager = db
        self.missing_words_dict: dict[str, list[Segment]] = {}
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

        self.ui.update_preprocessed_count(
            f"{len(self.preprocessed_dict)} / {len(self.missing_words_dict)}"
        )

    def preprocess_book(self, book: str):
        self.stop_flag = False

        # should only run once
        if not self.db.all_inflections:
            self.ui.update_message("Loading database...")
            self.db.make_inflections_lists()

        self.book = book
        self.load_preprocessed()
        self.find_missing_words_in_cst()
        self.find_missing_words_in_sutta_central()
        for self.word_in_text, self.sentence_data in self.missing_words_dict.items():
            self.ui.update_message(f"Processing {self.word_in_text}")

            self.related_entries_list = self.db.get_related_dict_entries(
                self.word_in_text
            )
            self.compile_prompt()
            self.response = str(self.send_prompt())
            self.update_preprocessed()
            if self.stop_flag:
                break

        self.ui.clear_all_fields()

    def is_missing(self, word: str):
        if (
            word not in self.db.all_inflections
            and word not in self.db.sandhi_ok_list
            and word not in self.preprocessed_keys
        ):
            return True
        else:
            return False

    def find_missing_words_in_cst(self) -> None:
        """Find all the missing words in CST."""

        self.ui.update_message("Finding missing words in CST")

        all_cst_words = make_cst_text_list(["vin3"])
        for word in all_cst_words:
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
14. comments

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
                # mdoel="deepseek-reasoner",
                prompt=self.prompt,
                prompt_sys="Follow the instructions very carefully.",
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
            if len(self.sentence_data) > 0:
                first_sentence = self.sentence_data[0]
                self.preprocessed_dict[self.word_in_text]["example_1"] = (
                    first_sentence.pali
                )
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
            self.ui.update_preprocessed_count(
                f"{len(self.preprocessed_dict)} / {len(self.missing_words_dict)}"
            )
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
