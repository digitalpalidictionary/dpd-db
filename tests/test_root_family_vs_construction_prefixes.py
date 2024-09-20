#!/usr/bin/env python3

"""Test if root family prefix == construction prefixes"""


import re

from rich import print
from typing import Optional
from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.meaning_construction import clean_construction
from tools.paths import ProjectPaths

class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    i: DpdHeadword
    constr_no_root_or_base: Optional[str]
    root_fam_prefix: Optional[str]
    construc_prefix: Optional[str]

    def update_prog_data(self, i):
        self.i = i
        self.constr_no_root_or_base = None
        self.root_fam_prefix = None
        self.construc_prefix = None


def main():
    pd = ProgData()
    for i in pd.db:
        pd.update_prog_data(i)
        test_logic(pd)


def test_logic(pd):
        if pd.i.root_key:
            if pd.i.root_key and pd.i.meaning_1:
                make_root_family_prefix(pd)
                if pd.i.root_base:
                    make_construction_without_base(pd)
                    if pd.root_fam_prefix != pd.construc_prefix:
                        fix_root_or_construction(pd)
                else:
                    make_construction_without_root(pd)
                    if pd.root_fam_prefix != pd.construc_prefix:
                        fix_root_or_construction(pd)
                    
                        
def fix_root_or_construction(pd):
    printer(pd)
    print("[cyan]change the [white]r[cyan]oot family or [white]c[cyan]onstruction? ", end="")
    route = input()

    if route == "r":
        print(f"[green]{'enter the new root family':<40}", end="")
        new_root_family = input()
        if new_root_family:
            print(f"[green]{'change the root family from':<40}", end="")
            print(f"[cyan]{pd.i.family_root}[/cyan]")
            print(f"[green]{'to':<40}", end="")
            print(f"[yellow]{new_root_family}")
            print(f"[green]{'y/n':<40}", end="")
            confirm = input()
            if confirm == "y":
                pd.i.family_root = new_root_family
                pd.db_session.commit()
                print("[green]family root updated in db!")
                test_logic(pd)

    if route == "c":
        print(f"[green]{'enter the new construction':<40}", end="")
        new_construction = input()
        if new_construction:
            print(f"[green]{'change the construction from':<40}", end="")
            print(f"[cyan]{pd.i.construction}[/cyan]")
            print(f"[green]{'to':<40}", end="")
            print(f"[yellow]{new_construction}")
            print(f"[green]{'y/n':<40}", end="")
            confirm = input()
            if confirm == "y":
                pd.i.construction = new_construction
                pd.db_session.commit()
                print("[green]construction updated in db!")
                test_logic(pd)


def make_root_family_prefix(pd):
    pd.root_fam_prefix = \
        re.sub("√.+$", "", pd.i.family_root)\
        .strip()


def make_construction_without_root(pd):
    constr_clean = clean_construction(pd.i.construction)
    pd.constr_no_root_or_base = re.sub("√.+$", "", constr_clean)
    make_construction_prefix(pd)


def make_construction_without_base(pd):
    # remove base types: pass, caus, denom etc.
    base_clean = re.sub(" \\(.+\\)$", "", pd.i.root_base)
    
    # remove base root + sign
    base = re.sub("(.+ )(.+?$)", "\\2", base_clean)
    
    # construction without '>' etc
    constr_clean = clean_construction(pd.i.construction)

    # remove base onwards from construction
    constr_no_base = re.sub(f"{base}.+$", "", constr_clean)
    
    pd.constr_no_root_or_base = constr_no_base

    make_construction_prefix(pd)


def make_construction_prefix(pd):
    c = pd.constr_no_root_or_base
    
    # remove other prefix and plus space
    c = re.sub("\\?\\?", "", c)
    c = re.sub("^na \\+ ", "", c)
    c = re.sub("^na \\+ ", "", c)
    c = re.sub("^a \\+ ", "", c)
    c = re.sub("^su \\+ ", "", c)
    c = re.sub("^dur \\+ ", "", c)
    c = re.sub("^sa \\+ sa \\+ ", "", c)
    c = re.sub("^sa \\+ ", "", c)
    c = re.sub("^ku \\+ ", "", c)
    c = re.sub("^nir \\+ ku \\+ ", "", c)
    c = re.sub("^nir \\+ ", "", c)

    # remove ' a ' in the middle
    c = re.sub(" a \\+", "", c)

    # change ' + ' to ' ' 
    c = re.sub(" \\+ ", " ", c)
    
    # remove final ' + '
    c = re.sub(" \\+ $", "", c)

    # remove brackets
    c = c.replace("(", "").replace(")", "")

    # and finally strip
    c = c.strip()

    pd.construc_prefix = c


def printer(pd):
    print("_"*50)
    print()
    print(f"[green]{'i.id':<40}[white]{pd.i.id}")
    print(f"[green]{'i.lemma_1':<40}[white]{pd.i.lemma_1}")
    print(f"[green]{'i.pos':<40}[white]{pd.i.pos}")
    print(f"[green]{'i.family_root':<40}[white]{pd.i.family_root}")
    print(f"[green]{'i.construction':<40}[white]{pd.i.construction}")
    print(f"[green]{'root_fam_prefix':<40}[white]'{pd.root_fam_prefix}'")
    print(f"[green]{'construc_prefix':<40}[white]'{pd.construc_prefix}'")
    print()

if __name__ == "__main__":
    main()
