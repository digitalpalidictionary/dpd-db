"""Go thru each word and its components in a text to find missing examples."""

import pickle
import pyperclip
import re

from rich import print
from typing import Dict, List, Tuple

from db.get_db_session import get_db_session
from db.models import PaliWord, InflectionToHeadwords, Sandhi
from tools.paths import ProjectPaths

from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_sc_text_sets import make_sc_text_list
from tools.source_sutta_example import find_source_sutta_example
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_list_sorter


class ProgData():
    tried_dict_path = "temp/pass2_dict/"
    def __init__(self, book: str) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.book = book
        self.tried_dict: dict = self.load_tried_dict()
        self.word_list: List[str] = make_text_list(self.pth, self.book)
        # self.word_list = ["ovadatīti"]
        
    def load_tried_dict(self):
        try:
            with open(self.pth.tried_dict_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {self.book: dict()}
    
    def update_tried_dict(self, wd) -> None:
        if self.book not in self.tried_dict:
            self.tried_dict[self.book] = {}
        if wd.word not in self.tried_dict[self.book]:
            self.tried_dict[self.book][wd.word] = {}
        if wd.headword not in self.tried_dict[self.book][wd.word]:
            self.tried_dict[self.book][wd.word][wd.headword] = set()
        self.tried_dict[self.book][wd.word][wd.headword].add(wd.sutta_example)
        
        with open(self.pth.tried_dict_path, "wb") as f:
                pickle.dump(self.tried_dict, f)

class WordData():
    def __init__(self, word) -> None:
        self.word: str = word
        self.search_pattern: str = fr"(\s)({self.word})(\s|[.,;:!?])"  
        self.sutta_example: Tuple[str, str, str]
        self.source: str
        self.sutta: str
        self.example: str
        self.example_print: str
        self.headword: str
    
    def update_sutta_example(self, sutta_example):
        self.sutta_example = sutta_example
        self.source = sutta_example[0]
        self.sutta = sutta_example[1]
        self.example = sutta_example[2]
        self._example_to_print()

    def _example_to_print(self):
        self.example_print: str = self.example\
            .replace("[", "{")\
            .replace("]", "}")
        self.replace: str = fr"\1[cyan]{self.word}[/cyan]\3"
        self.example_print: str = re.sub(
            self.search_pattern,
            self.replace,
            self.example_print)

    def update_headword(self, headword):
        self.headword: str = headword


def main():
    book = "kn9"
    pd = ProgData(book)

    for word in pd.word_list:
        wd = WordData(word)   
        sutta_examples = find_source_sutta_example(
            pd.pth, pd.book, wd.search_pattern)

        if sutta_examples:
            for sutta_example in sutta_examples:
                wd.update_sutta_example(sutta_example)

                # check for headwords with no examples
                headwords_list = get_headwords(pd, wd)
                check_example_headword(pd, wd, headwords_list)

                # check for words in deconstructions with no examples
                headwords_list = get_deconstruction_headwords(pd, wd)
                check_example_headword(pd, wd, headwords_list)


# other possbilities:
# example is commentary
# words in  constructions
# subwords in consrtuctions

def check_example_headword(pd, wd, headwords_list):
    if headwords_list:
        for headword in headwords_list:
            wd.update_headword(headword)
            needs_example, pali_word = has_no_example(pd, wd)
            if (
                needs_example and pali_word
                and wd.sutta_example not in pd.tried_dict\
                    .get(pd.book, {})\
                    .get(wd.word, {})\
                    .get(wd.headword, set())
            ):  
                print_to_terminal(pd, wd, pali_word)


                
          
def print_to_terminal(pd, wd, pali_word):
    """Display the example and the headword in the terminal."""                  
    print("-"*50)
    print()
    print(f"[green]{wd.source} [dark_green]{wd.sutta}")
    print(f"[white]{wd.example_print}")
    print()
    print(f"[cyan]{pali_word.pali_1}: [blue3]{pali_word.pos}. [blue1]{make_meaning(pali_word)}")
    print()
    print("[grey54]y/n: ", end="")
    pyperclip.copy(wd.word)
    ask_to_add(pd, wd, pali_word)
    

def ask_to_add(pd, wd, pali_word):
    """Ask the user to add or not."""
    should_add = input("")
    if should_add == "n":
        pd.update_tried_dict(wd)
    elif should_add == "y":
        pyperclip.copy(pali_word.id)
        print()
        print(f"[cyan]{pali_word.pali_1} {pali_word.id} copied to clipboard")
        print("[grey54]press any key to continue...", end= "")
        input()
    
    
def make_text_list(pth, book):
    cst_text_list = make_cst_text_list(pth, [book])
    sc_text_list = make_sc_text_list(pth, [book])
    full_text_list = cst_text_list + sc_text_list

    # sp_mistakes_list = make_sp_mistakes_list(pth)
    # variant_list = make_variant_list(pth)

    text_set = set(cst_text_list) | set(sc_text_list)
    # text_set = text_set - set(sp_mistakes_list)
    # text_set = text_set - set(variant_list)
    return sorted(text_set, key=lambda x: full_text_list.index(x))


def get_headwords(pd, wd):
    """Get the headwords of an inflected word."""
    results = pd.db_session\
        .query(InflectionToHeadwords)\
        .filter_by(inflection=wd.word)\
        .first()
    if results:
        return results.headwords_list
    else:
        return None


def get_deconstruction_headwords(pd, wd):
    """Lookup in deconstructions and return a list of headwords."""
    results = pd.db_session\
        .query(Sandhi)\
        .filter_by(sandhi=wd.word)\
        .first()
    if results:
        deconstructions = results.split_list
        
        inflections = set()
        for d in deconstructions:
            inflections.update(d.split(" + "))
        
        headwords_list = set()
        for i in inflections:
            results = pd.db_session\
                .query(InflectionToHeadwords)\
                .filter_by(inflection=i)\
                .first()
            if results:
                headwords_list.update(results.headwords_list)
        return pali_list_sorter(list(headwords_list))
    else:
        return None

      


def has_no_example(pd: ProgData, wd: WordData) -> Tuple[bool, PaliWord | None]:
    pali_word = pd.db_session\
                    .query(PaliWord)\
                    .filter_by(pali_1=wd.headword)\
                    .first()
    if pali_word and not pali_word.example_1:
        return True, pali_word
    else:
        return False, None


if __name__ == "__main__":
    main()
