#!/usr/bin/env python3

"""Import meaning_2 to create links"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    csv_dict = read_tsv_dot_dict("temp/paliword _numbers_.tsv")
    count = 0

    for csv in csv_dict:
        db = db_session.query(DpdHeadword).filter(
            DpdHeadword.id == csv.id).first()
        if db.meaning_2 != csv.meaning_2:
            print(f"{db.lemma_1:<40}{db.meaning_2:<40} {csv.meaning_2}")
            db.meaning_2 = csv.meaning_2
            count += 1
        if db.family_set != csv.family_set:
            print(f"{db.lemma_1:<40}{db.family_set:<40} {csv.family_set}")
            db.family_set = csv.family_set
            count += 1
    
    print(count)

    db_session.commit()
    db_session.close()



if __name__ == "__main__":
    main()
