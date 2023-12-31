#!/usr/bin/env python3

"""Add TSV of Therigtha nuns names to db"""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict


def main():
    pth = ProjectPaths()

    db_session = get_db_session(pth.dpd_db_path)

    theris = read_tsv_dot_dict("temp/theris.tsv")

    for theri in theris:
        if theri.add != "n" and theri.add != "u":
            # find any matching pali_1 in the db
            search = db_session.query(PaliWord)\
                .filter(PaliWord.pali_1==theri.pali_1)\
                .first()
            if search:
                print(theri.pali_1)
                print(search)
                input()
            
            # create and populate PaliWord
            p = PaliWord()
            for key, value in theri.items():
                setattr(p, key, value)

            db_session.add(p)
    
    db_session.commit()

    db = db_session.query(PaliWord).all()
    for i in db:
        if i.id > 77232:
            print(i)


if __name__ == "__main__":
    main()
