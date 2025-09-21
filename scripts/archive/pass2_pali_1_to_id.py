#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Convert lemma_1 to id in various places."""

import json
import pickle
from copy import deepcopy

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


class GlobalVars:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    pali_to_id_dict: dict
    pass2_dict: dict


g = GlobalVars()


def make_pali_to_id_dict():
    pali_to_id_dict = {}
    for i in g.db:
        pali_to_id_dict[i.lemma_1] = i.id

    g.pali_to_id_dict = pali_to_id_dict


def get_pass2_dict():
    with open(g.pth.pass2_checked_path, "rb") as file:
        g.pass2_dict = pickle.load(file)


def main():
    make_pali_to_id_dict()
    get_pass2_dict()

    # pass2 structure
    # book : data1
    #   data1 : data2
    #       data2: word :tried

    g.pass2_dict["kn9"].pop("nami 1")

    pass2_dict = deepcopy(g.pass2_dict)

    for book, data in pass2_dict.items():
        if book != "last_word":
            print(f"{book=}")
            for inflection, data2 in data.items():
                # print(f"{inflection=}")
                for headword, tried in data2.items():
                    try:
                        g.pass2_dict[book][inflection][g.pali_to_id_dict[headword]] = (
                            list(tried)
                        )
                        g.pass2_dict[book][inflection].pop(headword)
                        # print(f"{headword=}")
                    except Exception:
                        print(book, inflection, headword)
                        g.pass2_dict[book][inflection].pop(headword)
                        print()

    print(g.pass2_dict)

    with open("scripts/pass2.json", "w") as file:
        json.dump(g.pass2_dict, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
