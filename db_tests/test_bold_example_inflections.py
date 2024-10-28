#!/usr/bin/env python3

"""Test the bold word in examples is an actual inflection of the headword."""

import json
import re
import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.pali_alphabet import pali_alphabet
from sqlalchemy.orm import joinedload
from tools.configger import config_test
from tools.printer import p_summary, p_title


def check_username():
    if config_test("user", "username", "deva"):
        return True
    else:
        return False

class GlobalVars():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    show_sbs_data: bool = check_username()
    if show_sbs_data:
        db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).all()
    else:
        db = db_session.query(DpdHeadword).all()
    
    pali_alphabet: list[str] = pali_alphabet
    i: DpdHeadword
    
    if show_sbs_data:
        fields: list[str] = ["sbs_example_1", "sbs_example_2", "sbs_example_3", "sbs_example_4"]
    else:
        fields: list[str] = ["example_1", "example_2"]
    field: str
    
    bold_words: list[str]
    bold_word: str
    clean_bold_word: str
    
    inflections_list: list[str]
    
    counter: int = 1
    counter_total: int = 1
    pass_no: str

    exit: bool = False

    def __init__(self) -> None:
        self.json : dict[str, list[str]] = self.load_json()


    def get_headword(self, id: int)-> DpdHeadword:
        result = self.db_session.query(DpdHeadword).filter_by(id=id).first()
        if result:
            return result
        else:
            return DpdHeadword()

    @property
    def count_string(self) -> str:
        return f"{self.counter} / {self.counter_total}"
    
    def load_json(self) -> dict[str, list[str]]:
        try :
            with open(self.pth.bold_example_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            print(e)
            return {}
        
    def save_json(self):
        with open(self.pth.bold_example_path, "w") as f:
            json.dump(self.json, f, ensure_ascii=False, indent=2)
    
    def update_json(self, id: int, inflection:str):
        try:
            self.json[str(id)].append(inflection)
        except KeyError:
            self.json[str(id)] = [inflection]
        self.save_json()


def find_all_bold_words(g):
    """Get All the bold words from the string."""
    g.bold_words = re.findall("<b>.+?<\\/b>", getattr(g.i, g.field))


def find_all_bold_words_sbs(g):
    """Get All the bold words from the string."""
    if g.i.sbs is not None:
        g.bold_words = re.findall("<b>.+?<\\/b>", getattr(g.i.sbs, g.field))
    else:
        g.bold_words = []


def get_inflections(g):
    """Get the inflections list."""
    g.inflections_list = g.i.inflections_list


def clean_bold_word(g: GlobalVars):
    g.clean_bold_word = g.bold_word\
    .replace("<b>", "")\
    .replace("</b>", "")\
    .replace("'", "")\
    .replace("-", "")\
    .strip()


def test1(g: GlobalVars):
    """Clean up the word from tags and internal punctuation.
    Test if there's something left"""

    if not g.clean_bold_word:
        printer(g, "test1")
        return
    else:
        test2(g)


def test2(g: GlobalVars):
    """test 2, non-pali characters in the word."""
    for char in g.clean_bold_word:
        if char not in g.pali_alphabet:
            printer(g, "test2")
            return
    test3(g)


def test3(g: GlobalVars):
    """test 3, clean bold is in inflections list."""
    if g.clean_bold_word in g.inflections_list:
        return
    else:
        test4(g)


def test4(g: GlobalVars):
    """"test 4, missing last letter is the problem."""
    for inflection in g.inflections_list:
        if re.findall(f"{g.clean_bold_word}.", inflection):
            return
    test5(g)


def test5(g: GlobalVars):
    """test 5, nasals in last position."""
    nasals = ["ṅ", "ñ", "ṇ", "n", "m"]
    if g.clean_bold_word[-1] in nasals:
        clean_bold_nasal = f"{g.clean_bold_word[:-1]}ṃ"
        if clean_bold_nasal in g.inflections_list:
            return
    test6(g)


def test6(g: GlobalVars):
    """test 6, ññ in last position."""
    if g.clean_bold_word[-2:] == "ññ":
        clean_bold_nasal = f"{g.clean_bold_word[:-2]}ṃ"
        if clean_bold_nasal in g.inflections_list:
            return
    test7(g)


def test7(g: GlobalVars):
    """test 7, double letters"""
    
    if g.bold_word[3] == g.bold_word[4]:
        g.counter_total += 1
        if g.pass_no == "pass2":
            sentence = getattr(g.i, g.field)
            fixed_bold = re.sub("(<b>)(.)(.)", r"\2\1\3", g.bold_word)
            fixed_sentence = sentence.replace(g.bold_word, fixed_bold)
            
            print()
            print("-"*50)
            print()
            p_summary("counter", g.count_string)
            p_summary("id", g.i.id)
            p_summary("lemma", g.i.lemma_1)
            p_summary("pos", g.i.pos)
            p_summary("meaning", g.i.meaning_combo)
            p_summary("column", g.field)
            print()
            print(
                sentence.replace(
                    g.bold_word, f"[yellow]{g.bold_word}[/yellow]"))
            print()
            print(
                sentence.replace(
                    g.bold_word, f"[cyan]{fixed_bold}[/cyan]"))
            print()
            print(f"replace [yellow]{g.bold_word}[/yellow] with ", end="") 
            print(f"[cyan]{fixed_bold}[/cyan]? ", end="")
            print("[yellow]y[/yellow]es ", end="")
            print("[yellow]n[/yellow]o ", end="")
            

            choice = input()
            if choice == "y":
                setattr(g.i, g.field, fixed_sentence)   
                g.db_session.commit()

                print()
                print("[yellow]test the word while you're here: ", end="")
                pyperclip.copy(g.i.id)
                input()
            else:
                test8(g)
        else:
            test8(g)

    else:
        test8(g)


def test8(g: GlobalVars):
    """test 8, last position is sandhi."""

    for inflection in g.inflections_list:
        infl_len = len(inflection)

        if g.clean_bold_word[:infl_len-1] == inflection[:-1]:

            if (
                inflection[-1] == "a"
                and g.clean_bold_word[-1] == "ā"
            ):
                return
            elif (
                inflection[-1] == "i"
                and g.clean_bold_word[-1] == "ī"
            ):
                return
            elif (
                inflection[-1] == "u"
                and g.clean_bold_word[-1] == "ū"
            ):
                return
            elif (
                inflection[-1] == "ṃ"
                and g.clean_bold_word[-1] == "m"
            ):
                return
            elif (
                inflection[-1] == "ṃ"
                and g.clean_bold_word[-1] == "n" # anāgatamaddhānan
            ):
                return

    printer(g, "test8")


def printer(g: GlobalVars, message):
    """Print out the problem and up the tally."""

    if g.pass_no == "pass2":

        print()
        print("-"*50)
        print()
        p_summary("counter", g.count_string)
        p_summary("id", g.i.id)
        p_summary("pos", g.i.pos)
        p_summary("meaning", g.i.meaning_combo)
        p_summary("test", message)
        p_summary("column", g.field)
        p_summary("lemma", f"[cyan]{g.i.lemma_1}")
        p_summary("clean bold", f"[chartreuse2]{g.clean_bold_word}")

        g.counter += 1
        pyperclip.copy(g.i.id)
        
        print("[yellow]p[/yellow]ass ", end="")
        print("e[yellow]x[/yellow]it ", end="")
        print("or any key to continue: ", end="")
        
        choice = input()
        if choice == "x":
            g.exit = True
        if choice == "p":
            g.update_json(g.i.id, g.clean_bold_word)
        
        # freshen the session to show updated
        # g.db_session = get_db_session(g.pth.dpd_db_path)
        # if updated := g.db_session.query(DpdHeadword).filter_by(id = g.i.id).first():
        #     g.i = updated

    else:
        g.counter_total += 1

def main():
    p_title("test bold in examples are real inflections")
    
    g = GlobalVars()

    for pass_no in ["pass1", "pass2"]:
        g.pass_no = pass_no
        
        for g.i in g.db:
            
            if g.exit:
                break

            if g.i.pos not in ["idiom"]:
                # search in a list of fields
                for field in g.fields:
                    
                    if g.exit:
                        break
                    
                    g.field = field
                    
                    if g.show_sbs_data:
                        find_all_bold_words_sbs(g)
                    else:
                        find_all_bold_words(g)
                    
                    get_inflections(g)
                    
                    for bold_word in g.bold_words:
                        
                        g.bold_word = bold_word
                        clean_bold_word(g)
                        
                        try:
                            pass_list = g.json[str(g.i.id)]
                        except KeyError:
                            pass_list = []
                        
                        if g.clean_bold_word not in pass_list:
                            test1(g)
                            if g.exit:
                                break
    

if __name__ == "__main__":
    main()
