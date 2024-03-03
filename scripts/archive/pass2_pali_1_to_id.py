#!/usr/bin/env python3

"""Convert lemma_1 to id in various places."""

from copy import deepcopy
import json
import pickle
from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.paths import ProjectPaths

class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    pali_to_id_dict: dict
    pass2_dict: dict

pd = ProgData()


def make_pali_to_id_dict():
    pali_to_id_dict = {}
    for i in pd.db:
        pali_to_id_dict[i.lemma_1] = i.id

    pd.pali_to_id_dict = pali_to_id_dict

def get_pass2_dict():
    with open(pd.pth.pass2_checked_path, "rb") as file:
        pd.pass2_dict = pickle.load(file)


def main():
    make_pali_to_id_dict()
    get_pass2_dict()

    # pass2 structure 
    # book : data1
    #   data1 : data2
    #       data2: word :tried 

    pd.pass2_dict["kn9"].pop("nami 1")

    pass2_dict = deepcopy(pd.pass2_dict)

    for book, data in pass2_dict.items():
        if book != "last_word":
            print(f"{book=}")
            for inflection, data2 in data.items():
                # print(f"{inflection=}")
                for headword, tried in data2.items():
                    try:
                        pd.pass2_dict[book][inflection][pd.pali_to_id_dict[headword]] = list(tried)
                        pd.pass2_dict[book][inflection].pop(headword)
                        # print(f"{headword=}")
                    except Exception:
                        print(book, inflection, headword)
                        pd.pass2_dict[book][inflection].pop(headword)
                        print()
    
    print(pd.pass2_dict)


    with open("scripts/pass2.json", "w") as file:
        json.dump(pd.pass2_dict, file, ensure_ascii=False, indent=4)








if __name__ == "__main__":
    main()
