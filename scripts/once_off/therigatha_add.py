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
        # find any matching pali_1 in the db
        result = db_session.query(PaliWord)\
            .filter(PaliWord.pali_1==theri.pali_1)\
            .first()
        
        if theri.add != "n" and theri.add != "u":
            # add_theri(db_session, theri)
            pass
        if theri.add == "u":
            update_theri(db_session, theri, result)

    # db_session.commit()

    # show_updates(db_session)


def update_theri(db_session, theri, db):
    if "name of a nun" in db.meaning_1:
        db.meaning_1 = db.meaning_1.replace("name of a nun", "name of an arahant nun")
        print(f"{db.pali_1:<20}[yellow]{db.meaning_1}")
    if db.notes:
        db.notes += f"\n{theri.notes}"
        print(f"{db.pali_1:<20}[cyan]{db.notes}")
    else:
        db.notes = theri.notes
        print(f"{db.pali_1:<20}[cyan]{db.notes}")
    if "great disciples" in db.family_set:
        db.family_set = "names of nuns; names of arahants; great disciples"
        print(f"{db.pali_1:<20}[green]{db.family_set}")
    elif db.pali_1 == "ambapālī":
        print(f"{db.pali_1:<20}[green]{db.family_set}")
    else:
        db.family_set = theri.family_set
        print(f"{db.pali_1:<20}[green]{db.family_set}")
    print()

def add_theri(db_session, theri):
  
    # create and populate PaliWord
    p = PaliWord()
    for key, value in theri.items():
        setattr(p, key, value)

    db_session.add(p)


def show_updates(db_session):
    db = db_session.query(PaliWord).all()
    for i in db:
        if i.id > 77232:
            print(i)


if __name__ == "__main__":
    main()
