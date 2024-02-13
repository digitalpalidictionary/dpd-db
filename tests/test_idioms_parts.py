#!/usr/bin/env python3

"""Find super long words and hyphenate them."""

from collections import OrderedDict, defaultdict
import json
import re
import pyperclip

from rich import print
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, FamilyIdiom, Lookup
from tools.paths import ProjectPaths
from tools.pali_alphabet import pali_alphabet
from tools.tic_toc import tic, toc
from tools.db_search_string import db_search_string


class ProgData():
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)
    # lookup_db = db_session.query(Lookup).all()
    headword_db: list[DpdHeadwords] = db_session.query(DpdHeadwords).all()
    idioms_table_list: list[str] = []
    words_in_idioms_list: list[str] 


def make_idioms_table_list(g):
    """Make a list of all worsd in the idioms table"""
    print(f"[green]{'making a list of all words in idioms table':<40}", end="")

    idioms_table: list[FamilyIdiom] = g.db_session.query(FamilyIdiom).all()
    
    for i in idioms_table:
        g.idioms_table_list.append(i.idiom)
    print(len(g.idioms_table_list))


def make_words_in_idioms_list(g):
    """"Make a dict of all words in idioms."""
    print(f"[green]{'making dict of all words in idioms':<40}", end="")

    g.words_in_idioms_list = []
    for i in g.headword_db:
        if i.pos == "idiom":
            for part in i.lemma_clean.split(" "):
                g.words_in_idioms_list.append(part)
    print(len(g.words_in_idioms_list))


def find_headwords_add_idiom(g):
    """Find the headword and add the idiom."""
    print(f"[green]{'finding headwords and adding parts':<40}")

    for i in g.headword_db:
        if (
            i.pos == "idiom"
            and i.family_idioms
        ):
            print(f"[white]{i.lemma_1}")
            print(f"[green4]{i.family_idioms}")
            for part in i.lemma_clean.split(" "):
                print(f"  [spring_green4]{part}")

                lookup = g.db_session.query(Lookup).filter_by(lookup_key=part).first()
                ids = lookup.unpack_headwords()
                filter_headwords: list[DpdHeadwords] = g.db_session \
                    .query(DpdHeadwords) \
                    .filter(DpdHeadwords.id.in_(ids)) \
                    .all()
                for h in filter_headwords:
                    print(h)
                    if h.lemma_clean in g.idioms_table_list:
                        pass
                    else:
                        print("deal with me")
                        input()

            



def main():
    tic()
    print("[bright_yellow]finding parts of idioms for increased recognition")
    g = ProgData()
    make_idioms_table_list(g)
    make_words_in_idioms_list(g)
    find_headwords_add_idiom(g)


if __name__ == "__main__":
    main()
