#!/usr/bin/env python3

"""Find words with ID upto 71509 which are not in alphabetical order."""

import json
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    out_of_place = []

    for i in range(1, len(db)):
        if db[i].id < 71508:
            first_letter = db[i].lemma_1[0]
            next1_letter =  db[i+1].lemma_1[0]
            next2_letter = db[i+2].lemma_1[0]
            if (
                first_letter != next1_letter
                and next1_letter != next2_letter
            ):
                print(db[i-1].id, db[i-1].lemma_1)
                print(db[i].id, db[i].lemma_1)
                print(db[i+1].id, db[i+1].lemma_1)
                print(db[i+2].id, db[i+2].lemma_1)
                print()
                out_of_place.append(db[i+1].id)

    last_id = db[-1].id
    next_id = last_id + 1
    print("last id: ", last_id)
    print("next id: ", next_id)
    print()

    id_dict = {}

    for i in db:
        if i.id in out_of_place:
            id_dict[i.id] = next_id
            i.id = next_id
            print(i)
            next_id += 1
    
    db_session.commit()
    
    with open("temp/id_dict.json", "w") as f:
        json.dump(id_dict, f, indent=2)
    

if __name__ == "__main__":
    main()
