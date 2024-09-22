#!/usr/bin/env python3

"""Fill in the missing details of auto-added monks' names in Theragāthā"""


import pickle
import pyperclip

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.goldendict_tools import open_in_goldendict
from tools.paths import ProjectPaths




def main():
    print("[bright_yellow]fill details of theragāthā monks")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    # load previous set or start a new one
    try:
        done_list = load_pickle()
    except FileNotFoundError:
        done_list = []

    first = 76179
    last = 76417
    processed = len(done_list)
    total = last - first + 1

    print_done(done_list)
    print("Press any key to contine or X to exit")

    for counter, i in enumerate(db):
        if (
            first <= i.id <= last
            and i.id not in done_list
        ):
            pyperclip.copy(i.id)
            open_in_goldendict(i.lemma_clean)
            
            processed = len(done_list)
            print(f"{processed + 1:>3}/{total:<3} [green]{counter:<6}{i.lemma_1}", end=" ")
            inp = input()

            if inp == "x":
                break
            else:
                done_list += [i.id]

    print_done(done_list)
    dump_pickle(done_list)


def load_pickle():
    with open("tests/tests/theragatha_filler", "rb") as f:
        return pickle.load(f)


def dump_pickle(done_list):
        with open("tests/test_theragatha_filler", "wb") as f:
            pickle.dump(done_list, f)


def print_done(done_list):
    print(f"completed: {len(done_list)}")
    

if __name__ == "__main__":
    main()
