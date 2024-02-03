#!/usr/bin/env python3

"""Find super long words and hyphenate them."""

import json
import re
import pyperclip
import subprocess

from rich import print
from typing import Optional

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths
from tools.pali_alphabet import pali_alphabet
from tools.tic_toc import tic, toc
from tools.db_search_string import db_search_string



class ProgData():
    def __init__(self) -> None:
        self.max_length: int = 30
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(PaliWord).all()
        self.clean_words_set: set
        self.long_words_set: set
        self.variations_dict: dict
        self.spelling_chosen: Optional[str] = None
        self.spelling_other: Optional[list[str]] = None
        self.yes_no: str = "[white]y[green]es [white]n[green]o "
        self.hyphenations_dict: dict[str, str] = self.load_hyphenations_dict()

    def load_hyphenations_dict(self):
        if self.pth.hyphenations_dict_path.exists():
            with open(self.pth.hyphenations_dict_path) as file:
                return json.load(file)
        else:
            return {}

    def save_hyphenations_dict(self):
        with open(self.pth.hyphenations_dict_path, "w") as file:
            json.dump(
                self.hyphenations_dict, file, 
                ensure_ascii=False, indent=4)
    
    def update_hyphenations_dict(self, clean_word, dirty_word):
        if clean_word in self.hyphenations_dict:
            print("[red]replacing entry in [white]test_hyphenations.json")
            print(f"{clean_word}: {self.hyphenations_dict[clean_word]}")
            print("[red]with")
            print(f"[light_green]{clean_word}: {dirty_word}")
        self.hyphenations_dict[clean_word] = dirty_word
        self.save_hyphenations_dict()

    

def main():
    tic()
    print("[bright_yellow]testing and correcting hyphenation of long words")
    print()
    pd = ProgData()

    subprocess.Popen(
        ["code", pd.pth.hyphenations_dict_path])

    subprocess.Popen(
        ["code", pd.pth.hyphenations_scratchpad_path]) 

    extract_clean_words(pd)
    find_long_words(pd)
    find_variations(pd)
    process_long_words(pd)
    toc()
    
    
def extract_clean_words(pd):
    """extract all clean words from the db in examples and commentary."""
    print("[green]exatrcting words from db")

    # compile regex of pali_alphabet space apostrope dash 
    regex_compile = re.compile(f"[^{'|'.join(pali_alphabet)}| |'|-]")
    
    clean_words_set: set = set()
    for i in pd.db:
        for column in ["example_1", "example_2", "commentary"]:
            cell = getattr(i, column)
            clean_cell = cell.replace("<b>", "").replace("</b>", "")
            clean_cell = re.sub(regex_compile, " ", clean_cell)
            clean_words_set.update(clean_cell.split(" "))
    
    pd.clean_words_set = clean_words_set


def find_long_words(pd):
    """Find all the long words"""
    print("[green]finding long words")
    
    long_words_set: set = set()
    for word in pd.clean_words_set:
        if len(word) > pd.max_length:
            long_words_set.add(word)
    
    pd.long_words_set = long_words_set


def find_variations(pd):
    """Find apostophe and hyphenation variations in long words."""
    print("[green]finding apostophe and hyphenation variations")
    
    # compile regex of only pali_alphebet
    regex_compile = re.compile(f"[^{'|'.join(pali_alphabet)}]")
    
    variations_dict: dict = {}
    for dirty_word in pd.long_words_set:
        clean_word = re.sub(regex_compile, "", dirty_word)

        # test it's not a known hyphenation
        if (
            clean_word not in pd.hyphenations_dict
            and pd.hyphenations_dict.get(clean_word, None) != dirty_word
        ):
            # add to or update variations_dict
            if clean_word not in variations_dict:
                variations_dict[clean_word] = set([dirty_word])
            else:
                variations_dict[clean_word].update([dirty_word])
    
    # turn the variations into list so that they are subscriable
    for key, values in variations_dict.items():
        variations_dict[key] = list(set(values))

    pd.variations_dict = variations_dict


# FIXME 
# what about the case where the hyphenation differs from the saved version??

def process_long_words(pd):
    """process long words without hyphenation or with multiple versions"""
    print("[green]showing clean words and dirty variations")

    for counter, (clean_word, dirty_words) in enumerate(pd.variations_dict.items()):
        if clean_word not in pd.hyphenations_dict:
            print("_"*50)
            print()
            print(f"{counter} / {len(pd.variations_dict)}")
            print(f"[green]{clean_word} [blue]{len(clean_word)}")
            
            pd.spelling_chosen = None
            pd.spelling_other = None
            
            for dcount, dirty_word in enumerate(dirty_words):
                print(f"{dcount+1} [light_green]{dirty_word} [blue]{len(dirty_word)}")
            print()

            print("[green]which version would you like? number [white]m[/white]anual [white]o[/white]k e[white]x[/white]it ", end="")
            choice = input()
            print()
            
            if choice.isdigit():
                chosen_word = dirty_words[int(choice)-1]
                
                pd.spelling_clean = clean_word
                pd.spelling_chosen = chosen_word
                pd.spelling_other = [clean_word]
                pd.spelling_other.extend(dirty_words)
                pd.spelling_other.remove(chosen_word)
                pd.spelling_other = list(set(pd.spelling_other))

                replace_word_in_db(pd)
            
            elif choice == "m":
                dirty_words_str = '\n'.join(dirty_words)
                
                with open(pd.pth.hyphenations_scratchpad_path, "w") as file:
                    file.write(f"{clean_word}\n{dirty_words_str}")                                
                pyperclip.copy(f"{clean_word}\n{dirty_words_str}")
                
                print("[green]words copied clipboard & text file")
                print("[green]please paste your preferred version")
                chosen_word = input()
                
                chosen_word_clean = chosen_word.replace("-", "").replace("'", "")
                if chosen_word_clean == clean_word:
                    pd.spelling_clean = clean_word
                    pd.spelling_chosen = chosen_word
                    pd.spelling_other = [clean_word]
                    pd.spelling_other.extend(dirty_words)
                    pd.spelling_other = list(set(pd.spelling_other))

                    replace_word_in_db(pd)
                else:
                    print("[red]spelling error, better luck next time")
                    print()
            
            elif choice == "o":
                pd.update_hyphenations_dict(clean_word, dirty_words[0])
                print("[white]test_hyphenations.json [green]updated")
            
            elif choice == "x":
                break
        else:
            print(f"[red]{clean_word}[/red] already in [white]test_hyphenations.json")



def replace_word_in_db(pd):
    """Replace all variations with the preferred hyphenation."""

    id_list = []
    replacement_count = 0
    for i in pd.db:
        for field, field_name in [
            (i.example_1, "example_1"), 
            (i.example_2, "example_2"),
            (i.commentary, "commentary")
        ]:
            for replace_me in pd.spelling_other:
                if replace_me in field:
                    id_list += [i.id]

                    field_new = field.replace(replace_me, pd.spelling_chosen)
                    
                    field_old_highlight = field.replace(replace_me, f'[cyan]{replace_me}[/cyan]')
                    print(f"[green]{field_old_highlight}")
                    print()
                    
                    field_new_highlight = field_new.replace(pd.spelling_chosen, f"[cyan]{pd.spelling_chosen}[/cyan]")
                    print(f"[light_green]{field_new_highlight}")
                    print()

                    setattr(i, field_name, field_new)
                    replacement_count += 1
    
    print(f"[green]{replacement_count} replacement(s) made")
    
    if replacement_count > 0:
        pd.db_session.commit()
        pd.update_hyphenations_dict(pd.spelling_clean,pd.spelling_chosen)
        print("[green]committed to db and updated [light_green]test_hyphenations.json")
    
    else:
        print("[green]try manually replacing")
        id_list_string = db_search_string(id_list)
        pyperclip.copy(id_list_string)
        print("[green]db id's copied to clipboard")
        print(id_list_string)
        print(pd.spelling_other)
        print("[green]press any key to continue ", end="")
        input()
                

if __name__ == "__main__":
    main()
