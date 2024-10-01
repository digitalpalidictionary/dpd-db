#!/usr/bin/env python3
import re

from sqlalchemy import update

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def remove_space_in_family_word():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()

    add_to_db = []
    for __counter__, i in enumerate(dpd_db):

        if i.family_word is not None and " " in i.family_word:
            new_fw = re.sub("^.* ", "", i.family_word)
            print(f"{ i.family_word:>15} ---> {new_fw:<15}")

            add_to_db += [{"id": i.id, "family_word": new_fw}]

    print(add_to_db)
    db_session.execute(update(DpdHeadword), add_to_db)
    db_session.commit()
    db_session.close()


def main():
    remove_space_in_family_word()


if __name__ == "__main__":
    main()
