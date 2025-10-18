from pathlib import Path

import pyperclip
from bs4 import BeautifulSoup

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

files_to_process = [
    # DN
    Path("resources/dpd_submodules/cst/romn/s0101m.mul.xml"),
    Path("resources/dpd_submodules/cst/romn/s0102m.mul.xml"),
    Path("resources/dpd_submodules/cst/romn/s0103m.mul.xml"),
    # MN
    Path("resources/dpd_submodules/cst/romn/s0201m.mul.xml"),
    Path("resources/dpd_submodules/cst/romn/s0202m.mul.xml"),
    Path("resources/dpd_submodules/cst/romn/s0203m.mul.xml"),
]


def make_all_inflections_without_meaning_1():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_query = db_session.query(DpdHeadword).filter(DpdHeadword.meaning_1 == "").all()
    all_inflections_without_meaning_1 = set()

    for i in db_query:
        for inflection in i.inflections_list_all:
            all_inflections_without_meaning_1.add(inflection)
    return all_inflections_without_meaning_1


def make_all_subheadings_set():
    all_subheadings_set: set[str] = set()

    for file_path in files_to_process:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-16") as f:
                content = f.read()

            soup = BeautifulSoup(content, "xml")
            subheadings = soup.find_all("p", {"rend": "subhead"})

            for subhead in subheadings:
                text = subhead.get_text().strip()
                if text and text not in all_subheadings_set:
                    all_subheadings_set.add(text.lower())
    return all_subheadings_set


def print_missing_subheadings(subheading):
    print()
    print(subheading)
    pyperclip.copy(subheading)
    # open_in_goldendict_os(subheading)
    # input("press any key to continue...")


if __name__ == "__main__":
    # make a list of all inflections without meaning_1
    all_inflections_without_meaning_1: set[str] = (
        make_all_inflections_without_meaning_1()
    )

    # make a list of all subheadings
    all_subheadings_set: set[str] = make_all_subheadings_set()

    counter = 0
    for subheading in all_subheadings_set:
        if subheading in all_inflections_without_meaning_1:
            print_missing_subheadings(subheading)
            counter += 1
    print(counter)
