#!/usr/bin/env python3

"""find compounds with sukha and dukkha which don't have antonyms"""

import json
import re
import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.goldendict_tools import open_in_goldendict
from tools.paths import ProjectPaths
from tools.printer import p_green_title, p_title


def main():
    p_title("find sukha dukkha antonyms")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    tried = read_tried(pth)
    sukha_counter = 0
    dukkha_counter = 0
    for i in db:
        if test_sukh(i, tried):
            sukha_counter += 1
        if test_dukkh(i, tried):
            dukkha_counter += 1
    print(f"total sukha: {sukha_counter}")
    print(f"total dukkha: {dukkha_counter}")
    
    p_green_title("testing sukh")
    counter = 0
    for i in db:
        if test_sukh(i, tried):
            counter += 1
            pyperclip.copy(i.lemma_1)
            open_in_goldendict(i.lemma_1)
            print()
            print(f"{counter} / {sukha_counter}")
            print(f"{i.id:,}")
            print(f"[green]{i.lemma_1}")
            print("[red](e)xception or any other key to pass")
            choice = input()
            if choice == "e":
                tried.append(i.lemma_1)
                write_tried(pth, tried)
    
    p_green_title("testing dukkh")
    counter = 0
    for i in db:
        if test_dukkh(i, tried):
            counter += 1
            pyperclip.copy(i.lemma_1)
            open_in_goldendict(i.lemma_1)
            print()
            print(f"{counter} / {dukkha_counter}")
            print(f"{i.id:,}")
            print(f"[green]{i.lemma_1}")
            print("[red](e)xception or any other key to pass")
            choice = input()
            if choice == "e":
                tried.append(i.lemma_1)
                write_tried(pth, tried)        


def test_sukh(i, tried):
    if (
        re.findall("sukh", i.lemma_1)
        and not re.findall("sutta($| )", i.lemma_1)
        and "sukhum" not in i.lemma_1
        and "dukkh" not in i.lemma_1
        and "dukkh" not in i.antonym
        and i.lemma_1 not in tried
        and i.pos not in ["idiom", "sandhi"]
    ):
        return True
    else:
        return False


def test_dukkh(i, tried):
    if (
        re.findall("dukkh", i.lemma_1)
        and not re.findall("sutta($| )", i.lemma_1)
        and "udukkhal" not in i.lemma_1
        and "sukh" not in i.lemma_1
        and "sukh" not in i.antonym
        and i.lemma_1 not in tried
        and i.pos not in ["idiom", "sandhi"]
    ):
        return True
    else:
        return False


def read_tried(pth: ProjectPaths):
    try:
        with open(pth.sukha_dukkha_finder_path, "r") as f:
            tried = json.load(f)
    except Exception:
        tried = []
    return tried


def write_tried(pth: ProjectPaths, tried: list[str]):
    with open(pth.sukha_dukkha_finder_path, "w") as f:
        json.dump(tried, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
