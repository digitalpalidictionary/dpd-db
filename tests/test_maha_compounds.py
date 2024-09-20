#!/usr/bin/env python3

"""Test and update mahā compound_type and compound_construction"""

import json
import re
import pyperclip

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.printer import p_title


class GlobalVars:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    i: DpdHeadword
    compound_type: str
    compound_construction: str
    exit: bool = False
    process: bool = False
    maha_count: int = 0
    maha_count_total: int = 0

    def __init__(self) -> None:
        self.exceptions_list = self.load_exceptions_list()

    def load_exceptions_list(self):
        try:
            with open(self.pth.maha_exceptions_list) as f:
                return json.load(f)
        except:
            return []

    def save_exceptions_list(self):
        with open(self.pth.maha_exceptions_list, "w") as f:
            json.dump(self.exceptions_list, f)

    def add_exception(self):
        self.exceptions_list.append(self.i.id)
        self.save_exceptions_list()


def sort_maha(g: GlobalVars):
    """Find mahā in word and send for further processing"""

    if (
        g.i.lemma_1.startswith("mahā")
        and not g.i.compound_type
        and g.i.id not in g.exceptions_list
    ):
        g.process = True
    else:
        g.process = False


def process_maha(g: GlobalVars):
    """
    1. Add kammadhāraya to compound type
    2. Add compound construction
    3. Send for user to decide
    """

    g.maha_count += 1

    if g.i.lemma_clean.endswith("jātaka"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub("(.+)(jātaka)", r"\1 + \2", g.i.lemma_clean)

    elif g.i.lemma_clean.endswith("pāḷi"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub("(.+)(pāḷi)", r"\1 + \2", g.i.lemma_clean)

    elif g.i.lemma_clean.endswith("sutta"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub("(.+)(sutta)", r"\1 + \2", g.i.lemma_clean)

    elif g.i.lemma_clean.endswith("suttavaṇṇanā"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)(suttavaṇṇanā)", r"\1 + \2", g.i.lemma_clean
        )

    elif g.i.lemma_clean.endswith("ttheragāthā"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)t(theragāthā)", r"\1 + \2", g.i.lemma_clean
        )

    elif g.i.lemma_clean.endswith("ttherīgāthā"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)t(therīgāthā)", r"\1 + \2", g.i.lemma_clean
        )

    elif g.i.lemma_clean.endswith("therīgāthā"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)(therīgāthā)", r"\1 + \2", g.i.lemma_clean
        )

    elif g.i.lemma_clean.endswith("petivatthu"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)(petivatthu)", r"\1 + \2", g.i.lemma_clean
        )

    elif g.i.lemma_clean.endswith("petavatthu"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)(petavatthu)", r"\1 + \2", g.i.lemma_clean
        )

    elif g.i.lemma_clean.endswith("vimānavatthu"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)(vimānavatthu)", r"\1 + \2", g.i.lemma_clean
        )

    elif g.i.lemma_clean.endswith("vatthu"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub("(.+)(vatthu)", r"\1 + \2", g.i.lemma_clean)

    elif g.i.lemma_clean.endswith("vagga"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub("(.+)(vagga)", r"\1 + \2", g.i.lemma_clean)

    elif g.i.lemma_clean.endswith("sikkhāpada"):
        g.compound_type = "kammadhāraya"
        g.compound_construction = re.sub(
            "(.+)(sikkhāpada)", r"\1 + \2", g.i.lemma_clean
        )

    else:
        g.compound_construction = re.sub("(mahā)(.+)", r"\1 + \2", g.i.lemma_clean)
        g.compound_type = "kammadhāraya"
    monkey_decides(g)


def monkey_decides(g: GlobalVars):
    print(f"{g.maha_count} / {g.maha_count_total}")
    print(g.i.id, g.i.lemma_1, g.i.meaning_combo)
    print(f"{g.compound_type} ({g.compound_construction})")
    print("[cyan]o[/cyan]k", end=" ")
    print("[cyan]n[/cyan]o", end=" ")
    print("[cyan]e[/cyan]xception", end=" ")
    print("e[cyan]x[/cyan]it")
    print()
    pyperclip.copy(g.i.lemma_1)
    monkey_choice = input()
    if monkey_choice == "o":
        g.i.compound_type = g.compound_type
        g.i.compound_construction = g.compound_construction
    elif monkey_choice == "e":
        g.add_exception()
    elif monkey_choice == "x":
        g.exit = True


def count_mahas(g: GlobalVars):
    for g.i in g.db:
        sort_maha(g)
        if g.process:
            g.maha_count += 1
    print(f"{g.maha_count} words to process")
    print()
    g.maha_count_total = g.maha_count
    g.maha_count = 0


def commit_to_db(g: GlobalVars):
    print("commit to db?", end=" ")
    print("[cyan]y[/cyan]es", end=" ")
    print("[cyan]n[/cyan]o", end=" ")
    monkey_decides = input()
    if monkey_decides == "y":
        g.db_session.commit()
        print("committed ok")


def main():
    tic()
    p_title("test mahā in compounds")
    g = GlobalVars()

    count_mahas(g)

    for g.i in g.db:
        if g.exit:
            break
        else:
            sort_maha(g)
            if g.process:
                process_maha(g)
    
    commit_to_db(g)
    toc()


if __name__ == "__main__":
    main()
