#!/usr/bin/env python3.11
import re

from sqlalchemy import update

from db.get_db_session import get_db_session
from db.models import PaliWord


def remove_space_in_family_word():
    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(
        PaliWord
    ).all()

    add_to_db = []
    for counter, i in enumerate(dpd_db):

        if " " in i.family_word:
            new_fw = re.sub("^.* ", "", i.family_word)
            print(f"{ i.family_word:>15} ---> {new_fw:<15}")

            add_to_db += [{"id": i.id, "family_word": new_fw}]

    # print(add_to_db)
    db_session.execute(update(PaliWord), add_to_db)
    db_session.commit()
    db_session.close()


def main():
    remove_space_in_family_word()


if __name__ == "__main__":
    main()
