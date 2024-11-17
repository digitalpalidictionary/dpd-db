#!/usr/bin/env python3

"""Find super long words and hyphenate them."""

import json
import re
import subprocess
import pyperclip

from rich import print
from typing import Optional

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.pali_alphabet import pali_alphabet
from tools.tic_toc import tic, toc
from tools.db_search_string import db_search_string

max_length = 18
only_do_hyphenated_words = True
# True max_length =  18
# False max_length = 30


class GlobalVars():
    def __init__(self) -> None:
        self.max_length: int = max_length
        
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()
        self.hyphenations_dict: dict[str, str] = self.load_hyphenations_dict()
        
        self.clean_words_dict: dict
        self.hyphenated_words_dict: dict
        self.long_words_dict: dict
        self.variations_dict: dict

        self.ids: Optional[set] = None
        self.spelling_chosen: Optional[str] = None
        self.spelling_other: Optional[list[str]] = None
        self.spelling_clean: str = ""
        
        self.yes_no: str = "[white]y[green]es [white]n[green]o "
        

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
                ensure_ascii=False, indent=2)
    
    def update_hyphenations_dict(self, clean_word, dirty_word):
        if clean_word in self.hyphenations_dict:
            print("[red]replacing entry in [white]test_hyphenations.json")
            print(f"{clean_word}: {self.hyphenations_dict[clean_word]}")
            print("[red]with")
            print(f"[light_green]{clean_word}: {dirty_word}")
        self.hyphenations_dict[clean_word] = dirty_word
        self.save_hyphenations_dict()
 
    
def extract_clean_words(g: GlobalVars):
    """extract all clean words from the db in examples and commentary."""
    print("[green]extracting words from db")

    # compile regex of pali_alphabet space apostrophe dash 
    regex_compile = re.compile(f"[^{'|'.join(pali_alphabet)}| |'|-]")
    
    clean_words_dict: dict = {}
    for i in g.db:
        id = i.id
        for column in ["example_1", "example_2", "commentary"]:
            cell = getattr(i, column)
            clean_cell = cell.replace("<b>", "").replace("</b>", "")
            clean_cell = re.sub(regex_compile, " ", clean_cell)
            clean_words = clean_cell.split(" ")
            
            for clean_word in clean_words:
                if clean_word:
                    if clean_word not in clean_words_dict:
                        clean_words_dict[clean_word] = set([id])
                    else:
                        clean_words_dict[clean_word].add(id)

    g.clean_words_dict = clean_words_dict


def find_long_words(g: GlobalVars):
    """Find all the long words"""
    print("[green]finding long words")
    
    long_words_dict: dict = {}
    for word, ids in g.clean_words_dict.items():
        if len(word) > g.max_length:
            long_words_dict.update({word: ids})
    
    g.long_words_dict = long_words_dict


def find_hyphenated_words(g: GlobalVars):
    """Find all hyphenated words"""

    print("[green]finding hyphenated words")
    hyphenated_words_dict: dict = {}
    for word, ids in g.clean_words_dict.items():
        if "-" in word:
            hyphenated_words_dict.update({word: ids})
    
    g.hyphenated_words_dict = hyphenated_words_dict


def find_variations(g: GlobalVars):
    """Find apostrophe and hyphenation variations in long words."""
    print("[green]finding apostrophe and hyphenation variations")
    
    # compile regex of only pali_alphabet
    regex_compile = re.compile(f"[^{'|'.join(pali_alphabet)}]")
    
    variations_dict: dict = {}
    for dirty_word, ids in g.long_words_dict.items():
        clean_word = re.sub(regex_compile, "", dirty_word)

        # test it's not a known hyphenation
        if (
            clean_word not in g.hyphenations_dict
            and g.hyphenations_dict.get(clean_word, None) != dirty_word
        ):
            # add to or update variations_dict
            if clean_word not in variations_dict:
                variations_dict[clean_word] = {"dirty_words": set([dirty_word]), "ids": ids}
            else:
                variations_dict[clean_word]["dirty_words"].update([dirty_word])
                variations_dict[clean_word]["ids"].update(ids)
    
    # turn the variations into list so that they are subscriable
    for key, values in variations_dict.items():
            variations_dict[key]["dirty_words"] = list(set(values["dirty_words"]))

    g.variations_dict = variations_dict


# FIXME 
# what about the case where the hyphenation differs from the saved version??


def has_hyphenated_word(dirty_words):
    for word in dirty_words:
        if "-" in word:
            return True
    return False


def process_long_words(g: GlobalVars):
    """process long words without hyphenation or with multiple versions"""
    print("[green]showing clean words and dirty variations")

    # for counter, (clean_word, values) in enumerate(g.variations_dict.items()):
    for counter, (clean_word, values) in enumerate(g.variations_dict.items()):
        dirty_words = values["dirty_words"]
        g.ids = values["ids"]
        
        if clean_word not in g.hyphenations_dict:

            if (
                only_do_hyphenated_words 
                and not has_hyphenated_word(dirty_words)
            ):
                continue

            print("_"*50)
            print()
            print(f"{counter+1} / {len(g.variations_dict)}")
            print(f"[green]{clean_word} [blue]{len(clean_word)}")
            
            g.spelling_chosen = None
            g.spelling_other = None
            
            for dcount, dirty_word in enumerate(dirty_words):
                print(f"{dcount+1} [light_green]{dirty_word} [blue]{len(dirty_word)}")
            print()

            print("[green]which version would you like? number [white]m[/white]anual [white]o[/white]k [white]p[/white]ass e[white]x[/white]it ", end="")
            choice = input()
            print()
            
            if choice.isdigit() and dcount > 0:
                chosen_word = dirty_words[int(choice)-1]
                
                g.spelling_clean = clean_word
                g.spelling_chosen = chosen_word
                g.spelling_other = [clean_word]
                g.spelling_other.extend(dirty_words)
                g.spelling_other.remove(chosen_word)
                g.spelling_other = list(set(g.spelling_other))
                replace_word_in_db(g)
            
            elif choice == "m":
                dirty_words_str = '\n'.join(dirty_words)
                
                with open(g.pth.hyphenations_scratchpad_path, "w") as file:
                    file.write(f"{clean_word}\n{dirty_words_str}")                                
                pyperclip.copy(f"{clean_word}\n{dirty_words_str}")
                
                print("[green]words copied clipboard & text file")
                print("[green]please paste your preferred version")
                chosen_word = input()

                if chosen_word:
                    chosen_word_clean = chosen_word.replace("-", "").replace("'", "")
                    
                    if chosen_word_clean == clean_word:
                        g.spelling_clean = clean_word
                        g.spelling_chosen = chosen_word
                        g.spelling_other = [clean_word]
                        g.spelling_other.extend(dirty_words)
                        g.spelling_other = list(set(g.spelling_other))
                        replace_word_in_db(g)
                    
                    else:
                        print("[red]spelling error, better luck next time")
                        print()
                
                else:
                    print("[red]nothing pasted")
            
            elif (
                choice == "o"
                or choice.isdigit() and dcount == 0
            ):
                g.update_hyphenations_dict(clean_word, dirty_words[0])
                print("[white]test_hyphenations.json [green]updated")
            
            elif choice == "x":
                break

            elif choice == "p":
                continue

        else:
            print(f"[red]{clean_word}[/red] already in [white]test_hyphenations.json")


def replace_word_in_db(g: GlobalVars):
    """Replace all variations with the preferred hyphenation."""

    replacement_count = 0
    db_list = []
    for replace_me in g.spelling_other:
        db = g.db_session.query(DpdHeadword)\
            .filter(DpdHeadword.example_1.contains(replace_me)).all()
        db_list.extend(db)
        
        db = g.db_session.query(DpdHeadword)\
            .filter(DpdHeadword.example_2.contains(replace_me)).all()
        db_list.extend(db)
        
        db = g.db_session.query(DpdHeadword)\
            .filter(DpdHeadword.commentary.contains(replace_me)).all()
        db_list.extend(db)

        for i in db_list:

            for field, field_name in [
                (i.example_1, "example_1"), 
                (i.example_2, "example_2"),
                (i.commentary, "commentary")
            ]:

                if replace_me in field:
                    field_new = field.replace(replace_me, g.spelling_chosen)
                    
                    field_old_highlight = field.replace(replace_me, f'[cyan]{replace_me}[/cyan]')
                    print(f"[green]{field_old_highlight}")
                    print()
                    
                    field_new_highlight = field_new.replace(g.spelling_chosen, f"[cyan]{g.spelling_chosen}[/cyan]")
                    print(f"[light_green]{field_new_highlight}")
                    print()

                    setattr(i, field_name, field_new)
                    replacement_count += 1
    
    print(f"[green]{replacement_count} replacement(s) made")
    
    if replacement_count > 0:
        g.db_session.commit()
        g.update_hyphenations_dict(g.spelling_clean,g.spelling_chosen)
        print("[green]committed to db and updated [light_green]test_hyphenations.json")
    
    else:
        
        ids_str = db_search_string(g.ids)
        pyperclip.copy(ids_str)
        print("[green]try replacing manually, the db id's are copied to the clipboard")
        print("[green]press any key to continue ", end="")
        input()


def main():

    tic()
    print("[bright_yellow]testing and correcting hyphenation of long words")
    
    g = GlobalVars()

    subprocess.Popen(
        ["code", g.pth.hyphenations_dict_path])
    subprocess.Popen(
        ["code", g.pth.hyphenations_scratchpad_path]) 

    extract_clean_words(g)
    find_long_words(g)
    find_hyphenated_words(g)
    find_variations(g)
    process_long_words(g)
    
    toc()


if __name__ == "__main__":
    main()
