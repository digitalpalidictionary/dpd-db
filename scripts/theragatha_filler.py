#!/usr/bin/env python3

"""Fill in the missing details of auto-added monks' names in Theragāthā"""

import pickle
import pyperclip
import subprocess

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths

def open_in_goldendict(word: str) -> None:
    cmd = ["goldendict", word]
    subprocess.Popen(cmd)


def main():
    print("[bright_yellow]fill details of theragāthā monks")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    first = 76179
    last = 76417

    # load previous set or start a new one
    try:
        done_list = load_pickle()
    except FileNotFoundError:
        done_list = []
    print_done(done_list)

    for counter, i in enumerate(db):
        if (
            first <= i.id <= last
            and i.id not in done_list
        ):
            open_in_goldendict(i.pali_clean)
            print(counter, i.pali_1)
            pyperclip.copy(i.id)
            inp = input("Press any key to contine or X to exit: ")
            if inp == "x":
                break
            else:
                done_list += [i.id]

    print_done(done_list)
    dump_pickle(done_list)

def load_pickle():
    with open("scripts/theragatha_filler", "rb") as f:
        return pickle.load(f)

def dump_pickle(done_list):
        with open("scripts/theragatha_filler", "wb") as f:
            pickle.dump(done_list, f)


def print_done(done_list):
    print(f"completed: {done_list}")
    

if __name__ == "__main__":
    main()
