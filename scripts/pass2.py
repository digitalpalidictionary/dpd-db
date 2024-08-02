"""Go thru each word and its components in a text to find missing examples."""

import json
import pyperclip
import re
import sys

from rich import print
from typing import List

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.paths import ProjectPaths

from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_sc_text_sets import make_sc_text_list
from tools.cst_source_sutta_example import find_source_sutta_example
from tools.meaning_construction import make_meaning_combo
from tools.pali_sort_key import pali_list_sorter


class ProgData():
    def __init__(self, book: str) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.book = book
        self.tried_dict: dict = self.load_tried_dict()
        self.word_list: List[str] = make_text_list(self.pth, self.book)
        self.commentary_list: List[str] = [
            "VINa", "VINt", "DNa", "MNa", "SNa", "SNt", "ANa", 
            "KHPa", "KPa", "DHPa", "UDa", "ITIa", "SNPa", "VVa", "VVt",
            "PVa", "THa", "THIa", "APAa", "APIa", "BVa", "CPa", "JAa",
            "NIDD1a", "NIDD2a", "PMa", "NPa", "NPt", "PTP",
            "DSa", "PPa", "VIBHa", "VIBHt", "ADHa", "ADHt",
            "KVa", "VMVt", "VSa", "PYt", "SDt", "SPV", "VAt", "VBt",
            "VISM", "VISMa",
            "PRS", "SDM", "SPM",
            "bālāvatāra", "kaccāyana", "saddanīti", "padarūpasiddhi",
            "buddhavandana"
            ]
        self.exceptions: List[int] = [6664]
        
    def load_tried_dict(self):
        try:
            with open(self.pth.pass2_dict, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {self.book: dict()}

    def save_tried_dict(self) -> None:
        with open(self.pth.pass2_dict, "w") as f:
            json.dump(self.tried_dict, f, ensure_ascii=False, indent=2)
    
    def update_tried_dict(self, wd) -> None:
        if self.book not in self.tried_dict:
            self.tried_dict[self.book] = {}
        if wd.word not in self.tried_dict[self.book]:
            self.tried_dict[self.book][wd.word] = {}
        if wd.id not in self.tried_dict[self.book][wd.word]:
            self.tried_dict[self.book][wd.word][wd.id] = []
        self.tried_dict[self.book][wd.word][wd.id].append(wd.sutta_example)
        self.save_tried_dict()
    
    def update_last_word(self, wd) -> None:
        self.tried_dict["last_word"] = wd.word
        self.save_tried_dict()
        index = self.word_list.index(wd.word)
        total = len(self.word_list)
        counter = f"{index+1} / {total+12}"
        print("-"*50)
        print(f"[cyan]{counter:<12}[green]last word saved: [white]{wd.word}")


class WordData():
    def __init__(self, word) -> None:
        self.word: str = word
        self.search_pattern: str = fr"(^|\[|\{{|\s)({self.word})(\s|[.,;:!?]|\]|\}}$)"
        self.sutta_example: List[str]
        self.source: str
        self.sutta: str
        self.example: str
        self.example_print: str
        self.headword: str
        self.id: str
    
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

    def update_id(self, id):
        self.id: str = str(id)


def start_from_where(pd):
    """
    1. Start from the beginning
    2. or from the last saved word
    3. or from a specific word.
    """

    print("[green]1. start from the beginning")
    print("[green]2. start from the last saved word")
    print(f"[green]{'3. start from a specifc word':<40}", end="")
    user_input = input()
    
    if user_input == "2":
        last_word = pd.tried_dict["last_word"]
        index = pd.word_list.index(last_word)
        pd.word_list = pd.word_list[index:]
    
    elif user_input == "3":
        print(f"[green]{'start from which word?':<40}", end="")
        user_input = input()

        try:
            index = pd.word_list.index(user_input)
            pd.word_list = pd.word_list[index:]
        except ValueError:
            print(f"[bright_red]{user_input} not found in list")
            start_from_where(pd)


def main():
    print("[bright_yellow]pass2")
    book = "kn9"
    pd = ProgData(book)

    start_from_where(pd)

    for word in pd.word_list:
        wd = WordData(word)   
        sutta_examples = find_source_sutta_example(
            pd.book,
            wd.search_pattern
        )

        if sutta_examples:
            for sutta_example in sutta_examples:
                wd.update_sutta_example(list(sutta_example))

                # check for headwords with no examples
                headwords_list = get_headwords(pd, word)
                if headwords_list:
                    check_example_headword(pd, wd, headwords_list)

                # check for words in deconstructions with no examples
                headwords_list = get_deconstruction_headwords(pd, word)
                if headwords_list:
                    check_example_headword(pd, wd, headwords_list)
                
            pd.update_last_word(wd)
        
        else:
            print(f"[red]{'-'*50}")
            print(f"[red]no sutta example found for [bright_red]{word}")


def get_headwords(
        pd:ProgData,
        word_to_find: str
    ) -> List[str] | None:
    
    """Get the headwords of an inflected word."""
    
    results = pd.db_session\
        .query(InflectionToHeadwords)\
        .filter_by(inflection=word_to_find)\
        .first()
    if results:
        return results.headwords_list
    else:
        return None


def get_deconstruction_headwords(
        pd: ProgData,
        word_to_find: str
    ) -> List[str] | None:

    """Lookup in deconstructions and return a list of headwords."""

    results = pd.db_session\
        .query(Sandhi)\
        .filter_by(sandhi=word_to_find)\
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


def check_example_headword(
        pd: ProgData,
        wd: WordData,
        headwords_list: List[str]
    ) -> None:

    if headwords_list:
        for headword in headwords_list:
            wd.update_headword(headword)
            pali_word = pd.db_session\
                .query(DpdHeadwords)\
                .filter_by(lemma_1=wd.headword)\
                .first()
            if pali_word:
                wd.update_id(pali_word.id)

                # test not in tried_dict
                test1 = wd.sutta_example not in pd.tried_dict\
                        .get(pd.book, {})\
                        .get(wd.word, {})\
                        .get(wd.id, [])
                
                # test has no meaning and example
                test2 = has_no_meaning_or_example(pali_word)

                # test if can replace a commentary example 
                test3 = (
                    any(
                        item in pali_word.source_1
                        for item in pd.commentary_list)
                    ) and "(gram)" not in pali_word.meaning_1
                
                test4 = pali_word.id not in pd.exceptions

                if test1 and (test2 or test3) and test4:
                    print_to_terminal(pd, wd, pali_word)
            
            else:
                if "√" not in headword:
                    pali_word = DpdHeadwords()
                    print(headwords_list)
                    print(f"[red]{headword} not found")
                    print_to_terminal(pd, wd, pali_word)

            if pali_word:
                test_words_in_construction(pd, wd, pali_word)
                


def has_no_meaning_or_example(pali_word: DpdHeadwords
                              ) -> bool:
    """"Test the pali_word"""

    # needs an example
    condition_1 = pali_word and not pali_word.example_1

    # needs meaning_1
    condition_2 = pali_word and not pali_word.meaning_1

    if condition_1 or condition_2:
        return True
    else:
        return False
                
          
def print_to_terminal(pd: ProgData,
                      wd: WordData,
                      pali_word: DpdHeadwords
                      ) -> None:

    """Display the example and the headword in the terminal."""                  

    print("-"*50)
    print(f"{'word: ':<12}{wd.word}")
    print(f"{'headword: ':<12}{wd.headword}")
    print(f"{'id: ':<12}{wd.id}")
    print()
    print(f"[green]{wd.source} [dark_green]{wd.sutta}")
    print(f"[white]{wd.example_print}")
    print()
    print(f"[cyan]{pali_word.id} {pali_word.lemma_1}: [blue3]{pali_word.pos}. [blue1]{make_meaning_combo(pali_word)}")
    print()
    print("[white]y[grey54]es / [white]n[grey54]o / e[white]x[grey54]it: ", end="")
    pyperclip.copy(wd.word)
    ask_to_add(pd, wd, pali_word)
    

def ask_to_add(pd, wd, pali_word) -> None:
    """Ask the user to add or not."""
    should_add = input("")
    if should_add == "n":
        pd.update_tried_dict(wd)
    elif should_add == "y":
        pyperclip.copy(pali_word.id)
        print()
        print(f"[cyan]{pali_word.lemma_1} {pali_word.id} copied to clipboard")
        print("[grey54]press any key to continue...", end= "")
        input()
    elif should_add == "x":
        sys.exit()


def test_words_in_construction(
        pd: ProgData,
        wd:WordData,
        pali_word: DpdHeadwords
        ) -> None:

    if (
        pali_word
        and not pali_word.root_key
        and pali_word.construction
        and re.findall(r"\bcomp\b", pali_word.grammar)
    ):
        construction_clean = re.sub(
            r" >.+?\+ ", " + ", pali_word.construction)
        construction_parts = construction_clean.split(" + ")
        for word in construction_parts:
            headwords_list = get_headwords(pd, word)
            if headwords_list:
                check_example_headword(pd, wd, headwords_list)
    

def make_text_list(
        pth: ProjectPaths,
        book: str
        ) -> List[str]:
    cst_text_list = make_cst_text_list(pth, [book])
    sc_text_list = make_sc_text_list(pth, [book])
    full_text_list = cst_text_list + sc_text_list

    # sp_mistakes_list = make_sp_mistakes_list(pth)
    # variant_list = make_variant_list(pth)

    text_set = set(cst_text_list) | set(sc_text_list)
    # text_set = text_set - set(sp_mistakes_list)
    # text_set = text_set - set(variant_list)
    return sorted(text_set, key=lambda x: full_text_list.index(x))


if __name__ == "__main__":
    main()
