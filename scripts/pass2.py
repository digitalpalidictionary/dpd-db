"""Go thru each word and its components in a text to find missing examples."""

import pickle
import pyperclip
import re

from rich import print
from typing import Dict, List, Tuple

from db.get_db_session import get_db_session
from db.models import PaliWord, InflectionToHeadwords
from tools.paths import ProjectPaths

from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_sc_text_sets import make_sc_text_list
from tools.source_sutta_example import find_source_sutta_example
from tools.meaning_construction import make_meaning


class ProgData():
    tried_dict_path = "temp/pass2_dict/"
    def __init__(self, book: str) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.book = book
        self.tried_dict: dict = self.load_tried_dict()
        self.word_list: List[str] = make_text_list(self.pth, self.book)
        
    def load_tried_dict(self):
        try:
            with open(self.pth.tried_dict_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {self.book: dict()}
    
    def update_tried_dict(self, word, headword, sutta_example) -> None:
        if self.book not in self.tried_dict:
            self.tried_dict[self.book] = {}
        if word not in self.tried_dict[self.book]:
            self.tried_dict[self.book][word] = {}
        if headword not in self.tried_dict[self.book][word]:
            self.tried_dict[self.book][word][headword] = set()
        self.tried_dict[self.book][word][headword].add(sutta_example)
        
        with open(self.pth.tried_dict_path, "wb") as f:
                # print(self.tried_dict)
                pickle.dump(self.tried_dict, f)


def main():
    book = "kn9"
    pd = ProgData(book)

    for word in pd.word_list:
        pattern = fr"(^|\s){word}(\s|[.,;:!?]|$)"
        sutta_examples = find_source_sutta_example(pd.pth, pd.book, pattern)
        if sutta_examples:
            for sutta_example in sutta_examples:
                source, sutta, example = sutta_example
                example = example.replace("[", "{")
                example = example.replace("]", "}")
                replace = fr"\1[cyan]{word}[/cyan]\2"
                example = re.sub(pattern, replace, example)

                headwords = get_headwords(word, pd)
                if headwords:
                    for headword in headwords:
                        no_example, i = has_no_example(headword, pd)
                        if (
                            no_example and i
                            and sutta_example not in pd.tried_dict\
                                .get(book, {})\
                                .get(word, {})\
                                .get(headword, set())
                        ):
                            meaning = make_meaning(i)

                            print("-"*50)
                            print()
                            print(f"[green]{source} [dark_green]{sutta}")
                            print(f"[white]{example}")
                            print()
                            print(f"[cyan]{i.pali_1}: [blue3]{i.pos}. [blue1]{meaning}")
                            print()
                            print("[grey54]y/n: ", end="")
                            pyperclip.copy(word)
                            option = input("")
                            
                            if option == "n":
                                pd.update_tried_dict(word, headword, sutta_example)
                            
                            elif option == "y":
                                pyperclip.copy(i.id)
                                print()
                                print(f"[cyan]{i.pali_1} {i.id} copied to clipboard")
                                print("[grey54]press any key to continue...", end= "")
                                input()
                else:
                    # here needs to look in sandhi
                    pass

# other possbilities:
# example is commentary
# deconstructions
# word constructions
# subword consrtuctions
                
                
    
    
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


def get_headwords(word, pd):
    """Get the headwords of an inflected word."""
    results = pd.db_session\
        .query(InflectionToHeadwords)\
        .filter_by(inflection=word)\
        .first()
    if results:
        return results.headwords_list
    else:
        return None


def has_no_example(headword, pd) -> Tuple[bool, PaliWord | None]:
    headword_in_db = pd.db_session\
                    .query(PaliWord)\
                    .filter_by(pali_1=headword)\
                    .first()
    if headword_in_db and not headword_in_db.example_1:
        return True, headword_in_db
    else:
        return False, None


if __name__ == "__main__":
    main()
