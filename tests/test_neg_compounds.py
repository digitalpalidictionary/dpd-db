#!/usr/bin/env python3

"""Find negative kammadhārayas"""

import json
import re

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    exceptions_list: list[int]


def load_exceptions_list(g: ProgData):
    if g.pth.neg_compound_exceptions.exists():
        with open(g.pth.neg_compound_exceptions) as f:
            g.exceptions_list = json.load(f)
    else:
        g.exceptions_list = []


def add_exception(g: ProgData, id: int):
    g.exceptions_list.append(id)
    save_exceptions_list(g)


def save_exceptions_list(g: ProgData):
    with open(g.pth.neg_compound_exceptions, "w") as f:
        json.dump(g.exceptions_list, f, indent=2)

def main():
    tic()
    print("[bright_yellow]find negative kammadhārayas")
    g = ProgData()
    load_exceptions_list(g)

    for i in g.db:
        if (
            i.meaning_1
            and i.neg
            and re.findall("^na ", i.construction)
            and re.findall("\\bcomp\\b", i.grammar)
            and "kammadhāraya" not in i.compound_type
            and i.derivative != "taddhita"
            and i.pos not in ["abs", "ind", "prefix", "aor", "pr"]
            and i.id not in g.exceptions_list
        ):
            print("[magenta1]_"*50)
            print()
            print(f"[deep_pink2]{i.id}")
            print(f"[orange_red1]{i.lemma_1} {i.pos}")
            print(f"[indian_red1]{i.meaning_1}")
            print(f"[hot_pink]{i.construction}")
            if i.compound_construction:
                print(f"[medium_orchid1]{i.compound_type}[dark_orange] ({i.compound_construction})")
            print()
            print("[white]m[sandy_brown]anual [white]a[sandy_brown]utomatic [white]e[sandy_brown]xception", end=" ")
            route = input()
            
            if route:
                if route == "m":
                    print("[light_coral]enter compound construciton ", end="")
                    cc = input()
                    if cc:
                        i.compound_type = "kammadhāraya"
                        i.compound_construction = cc
                    else:
                        continue
                elif route == "a":
                    i.compound_type = "kammadhāraya"
                    i.compound_construction = auto_replace_na(i.lemma_clean)
                elif route == "e":
                    add_exception(g, i.id)
                    continue
                else:
                    print("unknown option")
                    continue

                print(f"[indian_red]{i.compound_type}")
                print(f"[hot_pink3]{i.compound_construction}")
                print()
                print("[pink3]press x to reject or any other key to continue", end=" ")
                route = input()
                if route == "x":
                    continue
                else:
                    g.db_session.commit()
    
    toc()


def auto_replace_na(lemma_clean: str) -> str:
    if lemma_clean.startswith("na"):
        # check if there's a double consonant
        if lemma_clean[2] == lemma_clean[3]:
            return f"na + {lemma_clean[3:]}"
        else:
            return f"na + {lemma_clean[2:]}"
    elif lemma_clean.startswith("an"):
        print("[light_coral]an or a?", end=" ")
        route = input()
        if route == "an":
            return f"na + {lemma_clean[2:]}"
        else:
            return f"na + {lemma_clean[1:]}"
    elif lemma_clean.startswith("a"):
        # check if there's a double consonant
        if lemma_clean[1] == lemma_clean[2]:
            return f"na + {lemma_clean[2:]}"
        else:
            return f"na + {lemma_clean[1:]}"
    elif lemma_clean.startswith("nā"):
        return f"na + a{lemma_clean[2:]}"
    else: 
        return ""


if __name__ == "__main__":
    main()

