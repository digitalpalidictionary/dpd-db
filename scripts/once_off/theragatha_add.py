#!/usr/bin/env python3

"""Add TSV of Theragtha monks' names to db"""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict


def main():
    pth = ProjectPaths()

    db_session = get_db_session(pth.dpd_db_path)

    theras = read_tsv_dot_dict("temp/theras.tsv")

    for thera in theras:
        if thera.add != "n":
            # find any matching pali_1 in the db
            search = db_session.query(PaliWord)\
                .filter(PaliWord.pali_1==thera.pali_1)\
                .first()
            if search:
                print(thera.pali_1)
                print(search)
                input()
            
            # create and populate PaliWord
            p = PaliWord()
            for key, value in thera.items():
                setattr(p, key, value)

            db_session.add(p)
    
    db_session.commit()

    db = db_session.query(PaliWord).all()
    for i in db:
        if i.id > 76170:
            print(i)


if __name__ == "__main__":
    main()
