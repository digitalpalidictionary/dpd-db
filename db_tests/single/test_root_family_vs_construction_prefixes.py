#!/usr/bin/env python3

"""Test if root family prefix == construction prefixes"""

import re
from typing import Optional

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


class GlobalVars:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db: list[DpdHeadword] = db_session.query(DpdHeadword).all()
    i: DpdHeadword
    constr_no_root_or_base: Optional[str]
    root_fam_prefix: Optional[str]
    construction_prefix: Optional[str]

    def update_prog_data(self, i):
        self.i = i
        self.constr_no_root_or_base = None
        self.root_fam_prefix = None
        self.construction_prefix = None


def main():
    g = GlobalVars()
    for i in g.db:
        g.update_prog_data(i)
        test_logic(g)


def test_logic(g: GlobalVars):
    if not (g.i.root_key and g.i.meaning_1):
        return

    make_root_family_prefix(g)

    if g.i.root_base:
        make_construction_without_base(g)
    else:
        make_construction_without_root(g)

    if g.root_fam_prefix != g.construction_prefix:
        fix_root_or_construction(g)
        return

    make_root_family_prefix(g)

    if g.i.root_base:
        make_construction_without_base(g)
    else:
        make_construction_without_root(g)

    if g.root_fam_prefix != g.construction_prefix:
        fix_root_or_construction(g)
        make_root_family_prefix(g)
        if g.i.root_base:
            make_construction_without_base(g)
            if g.root_fam_prefix != g.construction_prefix:
                fix_root_or_construction(g)
        else:
            make_construction_without_root(g)
            if g.root_fam_prefix != g.construction_prefix:
                fix_root_or_construction(g)


def fix_root_or_construction(g: GlobalVars):
    printer(g)
    print(
        "[cyan]change the [white]r[cyan]oot family or [white]c[cyan]onstruction? ",
        end="",
    )
    route = input()

    if route == "r":
        print(f"[green]{'enter the new root family':<40}", end="")
        new_root_family = input()
        if new_root_family:
            print(f"[green]{'change the root family from':<40}", end="")
            print(f"[cyan]{g.i.family_root}[/cyan]")
            print(f"[green]{'to':<40}", end="")
            print(f"[yellow]{new_root_family}")
            print(f"[green]{'y/n':<40}", end="")
            confirm = input()
            if confirm == "y":
                g.i.family_root = new_root_family
                g.db_session.commit()
                print("[green]family root updated in db!")
                test_logic(g)

    if route == "c":
        print(f"[green]{'enter the new construction':<40}", end="")
        new_construction = input()
        if new_construction:
            print(f"[green]{'change the construction from':<40}", end="")
            print(f"[cyan]{g.i.construction}[/cyan]")
            print(f"[green]{'to':<40}", end="")
            print(f"[yellow]{new_construction}")
            print(f"[green]{'y/n':<40}", end="")
            confirm = input()
            if confirm == "y":
                g.i.construction = new_construction
                g.db_session.commit()
                print("[green]construction updated in db!")
                test_logic(g)


def make_root_family_prefix(g: GlobalVars):
    g.root_fam_prefix = re.sub("√.+$", "", g.i.family_root).strip()


def make_construction_without_root(g: GlobalVars):
    constr_clean = g.i.construction_clean
    g.constr_no_root_or_base = re.sub("√.+$", "", constr_clean)
    make_construction_prefix(g)


def make_construction_without_base(g: GlobalVars):
    # remove base types: pass, caus, denom etc.
    base_clean = re.sub(" \\(.+\\)$", "", g.i.root_base)

    # remove base root + sign
    base = re.sub("(.+ )(.+?$)", "\\2", base_clean)

    # construction without '>' etc
    constr_clean = g.i.construction_clean

    # remove base onwards from construction
    constr_no_base = re.sub(f"{base}.+$", "", constr_clean)

    g.constr_no_root_or_base = constr_no_base

    make_construction_prefix(g)


def make_construction_prefix(g: GlobalVars):
    c = g.constr_no_root_or_base

    # remove other prefix and plus space
    c = re.sub("\\?\\?", "", c)
    c = re.sub("^na \\+ ", "", c)
    c = re.sub("^no \\+ ", "", c)
    c = re.sub("^na \\+ ", "", c)
    c = re.sub("^a \\+ ", "", c)
    c = re.sub("^su \\+ ", "", c)
    c = re.sub("^dur \\+ ", "", c)
    c = re.sub("^sa \\+ sa \\+ ", "", c)
    c = re.sub("^sa \\+ ", "", c)
    c = re.sub("^ku \\+ ", "", c)
    c = re.sub("^nir \\+ ku \\+ ", "", c)
    c = re.sub("^nir \\+ ", "", c)
    # c = re.sub("^ati \\+ ", "", c)

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

    g.construction_prefix = c


def printer(g: GlobalVars):
    print("_" * 50)
    print()
    print(f"[green]{'i.id':<40}[white]{g.i.id}")
    print(f"[green]{'i.lemma_1':<40}[white]{g.i.lemma_1}")
    print(f"[green]{'i.pos':<40}[white]{g.i.pos}")
    print(f"[green]{'i.family_root':<40}[white]{g.i.family_root}")
    print(f"[green]{'i.construction':<40}[white]{g.i.construction}")
    print(f"[green]{'root_fam_prefix':<40}[white]'{g.root_fam_prefix}'")
    print(f"[green]{'construc_prefix':<40}[white]'{g.construction_prefix}'")
    print()


if __name__ == "__main__":
    main()
