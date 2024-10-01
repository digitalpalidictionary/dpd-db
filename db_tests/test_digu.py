#!/usr/bin/env python3

"""Find numerals in compounds, and change the compound type to digu."""

import json
import re
import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_summary, p_title, p_yes


class GlobalVars():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    pass_no: str
    local_counter: int = 0
    total_counter: int = 0

    i: DpdHeadword
    
    cardinal_pali_set = set()
    cardinal_english_set = set()

    ordinal_pali_set = set()
    ordinal_english_set = set()

    meaning_parts: list[str]

    exit: bool = False

    def __init__(self) -> None:
        self.json : dict[int, str] = self.load_json()


    def load_json(self) -> dict[int, str]:
        try :
            with open(self.pth.digu_json_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            print(e)
            return {}
        
    def save_json(self):
        with open(self.pth.digu_json_path, "w") as f:
            json.dump(self.json, f, ensure_ascii=False, indent=2)
    
    def update_json(self):
        self.json[self.i.id] = self.i.lemma_1
        self.save_json()


def make_sets_of_cardinals_and_ordinals(g: GlobalVars):
    """Make a set of all cardinal and ordinal numbers in the db."""

    p_green("making sets of pali and english cardinals and ordinals")
    
    for i in g.db:
        if i.pos == "card":
            g.cardinal_pali_set.add(i.lemma_clean)
            clean_cardinal = re.sub(r" \(.+", "", i.meaning_combo)
            g.cardinal_english_set.add(clean_cardinal)
        if i.pos == "ordin":
            g.ordinal_pali_set.add(i.lemma_clean )
            clean_ordinal = re.sub(r" \(.+", "", i.meaning_combo)
            g.ordinal_english_set.add(clean_ordinal)

    p_yes(f"{len(g.cardinal_pali_set)}, {len(g.ordinal_pali_set)}")


def fix_kammadhāraya(g: GlobalVars):

    p_green_title("fix kammadhāraya")

    for g.pass_no in ["pass1", "pass2"]:
        for g.i in g.db:
            if g.exit:
                return
            if (
                g.i.pos not in ["card", "ordin"]
                and g.i.meaning_1
                and re.findall(r"\bcomp\b", g.i.grammar)
                and "kammadhāraya" in g.i.compound_type
                and str(g.i.id) not in g.json
            ):
                make_meaning_parts(g)
                if (
                    construction_contains_pali_cardinal(g) 
                    and meaning_contains_english_cardinal(g)
                    and meaning_contains_no_english_ordinal(g)
                ):
                    if g.pass_no == "pass1":
                        g.total_counter += 1
                        printer_pass1(g)
                    else:
                        g.local_counter += 1
                        printer_pass2(g)


def fix_no_compound(g: GlobalVars):

    p_green_title("fix those with no compound")

    for g.pass_no in ["pass1", "pass2"]:
        for g.i in g.db:
            if g.exit:
                return
            if (
                g.i.pos not in ["card", "ordin", "ind"]
                and g.i.meaning_1
                and re.findall(r"\bcomp\b", g.i.grammar)
                and not g.i.compound_type
                and str(g.i.id) not in g.json
            ):
                make_meaning_parts(g)
                if (
                    construction_contains_pali_cardinal(g) 
                    and meaning_contains_english_cardinal(g)
                    and meaning_contains_no_english_ordinal(g)
                ):
                    if g.pass_no == "pass1":
                        g.total_counter += 1
                        printer_pass1(g)
                    else:
                        g.local_counter += 1
                        printer_pass2(g)


def fix_other_compounds(g: GlobalVars):

    p_green_title("fix other compound types")

    for g.pass_no in ["pass1", "pass2"]:
        for g.i in g.db:
            if g.exit:
                return
            if (
                g.i.pos not in ["card", "ordin"]
                and g.i.meaning_1
                and re.findall(r"\bcomp\b", g.i.grammar)
                and g.i.compound_type
                and not re.findall("kammadhāraya|digu", g.i.compound_type)
                and str(g.i.id) not in g.json
            ):
                make_meaning_parts(g)
                if (
                    construction_contains_pali_cardinal(g) 
                    and meaning_contains_english_cardinal(g)
                    and meaning_contains_no_english_ordinal(g)
                ):
                    if g.pass_no == "pass1":
                        g.total_counter += 1
                        printer_pass1(g)
                    else:
                        g.local_counter += 1
                        printer_pass2(g)



def make_meaning_parts(g: GlobalVars):
    clean_meaning = re.sub(r"[;.-?()'!,√…]", "", g.i.meaning_1)
    g.meaning_parts = clean_meaning.split(" ")


def construction_contains_pali_cardinal(g: GlobalVars):
    """Test if the construction parts contain a pali cardinal"""
    
    construction_parts = g.i.construction_clean.split(" + ")

    for c in construction_parts:
        if c in g.cardinal_pali_set:
            return True
    return False


def meaning_contains_english_cardinal(g: GlobalVars):
    """Test if the meaning contain an english cardinal"""

    for m in g.meaning_parts:
        if m in g.cardinal_english_set:
            return True
    return False
        

def meaning_contains_no_english_ordinal(g: GlobalVars):
    """Test if the meaning contains no english ordinal"""

    for m in g.meaning_parts:
        if m in g.ordinal_english_set:
            return False
    return True
        

def printer_pass1(g: GlobalVars):
    print(f"{g.total_counter:<5}", end="")
    print(f"{g.i.id:<6}", end="")
    print(f"{g.i.lemma_1[:28]:<30}", end="")
    print(f"{g.i.pos:<10}", end="")
    print(f"{g.i.meaning_1[:48]:<50}", end="")
    print(f"{g.i.compound_type:<30}", end="")
    print(f"{g.i.compound_construction[:35]}")


def printer_pass2(g: GlobalVars):
    print()
    print("-"*50)
    print()
    p_summary("", f"{g.local_counter} / {g.total_counter}")
    p_summary("id", g.i.id)
    p_summary("lemma", g.i.lemma_1)
    p_summary("pos", g.i.pos)
    p_summary("meaning", g.i.meaning_1)
    p_summary("cp type", g.i.compound_type)
    p_summary("cp construction", g.i.compound_construction)
    
    print()
    print("[yellow]p[/yellow]ass ", end="")
    print("e[yellow]x[/yellow]it ", end="")
    print("or any key to continue: ", end="")
    pyperclip.copy(g.i.lemma_1)
    choice = input()
    if choice == "x":
        g.exit = True
    if choice == "p":
        g.update_json()


def main():
    p_title("find all digu samāsa")
    
    g = GlobalVars()
    make_sets_of_cardinals_and_ordinals(g)
    # fix_kammadhāraya(g)
    # fix_no_compound(g)
    fix_other_compounds(g)


if __name__ == "__main__":
    main()