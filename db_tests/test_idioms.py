#!/usr/bin/env python3

"""Test idioms to see that their component words contain the correct family idiom."""

from collections import defaultdict
import json
import re
import pyperclip

from rich import print
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyIdiom, Lookup
from tools.meaning_construction import clean_construction, make_meaning_combo
from tools.paths import ProjectPaths
from tools.goldendict_tools import open_in_goldendict

class ProgData():
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)
    idioms_table_list: list[str] = []
    words_in_idioms_dict: defaultdict = defaultdict(list[tuple[str, str, str]])
    headwords_db: list[DpdHeadword] = db_session.query(DpdHeadword).all()
    exceptions_dict: dict[str, list[int]]


def load_exceptions_dict(g: ProgData):
    if g.pth.idioms_exceptions_dict.exists():
        with open(g.pth.idioms_exceptions_dict) as f:
            g.exceptions_dict = json.load(f)
    else:
        g.exceptions_dict = {}


def add_exception(g: ProgData, idiom: str, id: int):
    if idiom in g.exceptions_dict:
        g.exceptions_dict[idiom] += [id]
    else:
        g.exceptions_dict[idiom] = [id]
    save_exceptions_dict(g)


def save_exceptions_dict(g: ProgData):
    with open(g.pth.idioms_exceptions_dict, "w") as f:
        json.dump(g.exceptions_dict, f, ensure_ascii=False, indent=2)


def make_idioms_table_list(g: ProgData):
    """Make a list of all worsd in the idioms table"""
    idioms_table: list[FamilyIdiom] = g.db_session.query(FamilyIdiom).all()
    for i in idioms_table:
        g.idioms_table_list.append(i.idiom)


def tupler(i: DpdHeadword):
    meaning = make_meaning_combo(i)
    return (i.lemma_1, meaning, i.family_idioms, i.family_compound)


def get_headword_ids(g: ProgData, key):
    lookup = g.db_session.query(Lookup)\
        .filter_by(lookup_key=key) \
        .filter(Lookup.headwords !="") \
        .first()
    
    if lookup:
        return lookup.headwords_unpack
    else:
        return []


def make_words_in_idioms_dict(g: ProgData):
    """Find all the idioms and their component words."""

    for i in g.headwords_db:
        if (
            i.pos == "idiom"
            and i.meaning_1
        ):
            for part in i.lemma_clean.split(" "):
                headwords_ids = get_headword_ids(g, part)
                for headword_id in headwords_ids:
                   g.words_in_idioms_dict[headword_id].append(tupler(i))


def add_words_in_compounds(g: ProgData):
    i: DpdHeadword
    for i in g.headwords_db:
        if i.id in g.words_in_idioms_dict:
            if re.findall("\\bcomp\\b", i.grammar):
                construction = clean_construction(i.construction)
                parts = construction.split(" + ")
                for part in parts:
                    headwords_ids = get_headword_ids(g, part)
                    for headword_id in headwords_ids:
                        g.words_in_idioms_dict[headword_id].append(tupler(i))


def add_family_idioms(g: ProgData):
    for i in g.headwords_db:
        if (
            not i.family_idioms
            and i.lemma_clean not in g.idioms_table_list 
        ):
            if i.id in g.words_in_idioms_dict:
                for idiom, meaning, family_idioms, family_compounds in g.words_in_idioms_dict[i.id]:
                    if i.id not in g.exceptions_dict.get(idiom, []):
                        print("_"*50)                
                        print()
                        print(f"[green]{'id':<30}[green1]{i.id}")
                        print(f"[green]{'lemma':<30}[green1]{i.lemma_1}")
                        print(f"[green]{'pos':<30}[green1]{i.pos}")
                        meaning_combo = make_meaning_combo(i)
                        print(f"[green]{'meaning':<30}[green1]{meaning_combo}")
                        print(f"[green]{'family_idioms':<30}[green1]{i.family_idioms}")
                        print(f"[green]{'family_compounds':<30}[green1]{i.family_compound}")
                        if i.family_compound:
                            pyperclip.copy(i.family_compound)
                        print()
                        # open_in_goldendict(str(i.id))

                        print(f"[green]{'idiom:':<30}[medium_spring_green]{idiom}")
                        print(f"[green]{'meaning:':<30}[spring_green1]{meaning}")
                        print(f"[green]{'family_idioms:':<30}[spring_green2]{family_idioms}")
                        print(f"[green]{'family_compounds:':<30}[spring_green2]{family_compounds}")
                        print()
                        message = "idiom or [white]e[green]xception"
                        print(f"[green]{message:<30}", end="            ")
                        idiom_to_add = input()

                        if idiom_to_add == "e":
                            add_exception(g, idiom, i.id)
                        
                        elif idiom_to_add:
                            i.family_idioms = idiom_to_add
                            g.db_session.commit()
                            print(f"[white]{idiom_to_add}[green] added to [white]{i.lemma_1}")
                            print()



def main():
    g = ProgData()
    load_exceptions_dict(g)
    make_idioms_table_list(g)
    make_words_in_idioms_dict(g)
    add_words_in_compounds(g)
    add_family_idioms(g)

if __name__ == "__main__":
    main()
