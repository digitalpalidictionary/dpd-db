#!/usr/bin/env python3

import sys

from typing import List

from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.sql import null
from sqlalchemy.sql.elements import and_

from dpd.models import PaliWord, PaliRoot
from dpd.db_helpers import create_db_if_not_exists, get_db_session

def add_roots(db_session: Session):
    items: List[PaliRoot] = []

    r = PaliRoot(
        root = "√kar 1",
        root_base = "karo, kās, kubba, kharo, kā (fut), kassa (fut), kāre (caus), kārāpe (caus), kariya (pass), karīya (pass)",
        root_meaning = "do, make",
    )
    items.append(r)

    r = PaliRoot(
        root = "√kar 2",
        root_base = null(),
        root_meaning = "love, pity",
    )
    items.append(r)

    try:
        for i in items:
            db_session.add(i)
        db_session.commit()
    except Exception as e:
        print(str(e))
        sys.exit(1)

def add_words(db_session: Session):
    items: List[PaliWord] = []

    w = PaliWord(
        pali1 = "karoti 1",
        pali2 = "karoti",
        pos = "pr",
        meaning1 = "does; acts; performs",
        meaning_lit = null(),
    )

    r = db_session.query(PaliRoot) \
        .filter(and_(
            PaliRoot.root == "√kar 1",
            PaliRoot.root_meaning == "do, make",
        )) \
        .first()

    if r is not None:
        w.pali_root = r

    items.append(w)

    w = PaliWord(
        pali1 = "akaronta 1",
        pali2 = "akaronta",
        pos = "prp",
        meaning1 = "not doing; not performing",
        meaning_lit = null(),
    )

    r = db_session.query(PaliRoot) \
        .filter(and_(
            PaliRoot.root == "√kar 1",
            PaliRoot.root_meaning == "do, make",
        )) \
        .first()

    if r is not None:
        w.pali_root = r

    items.append(w)

    try:
        for i in items:
            db_session.add(i)
        db_session.commit()
    except Exception as e:
        print(str(e))
        sys.exit(1)

def main():
    dpd_db_path = Path("dpd.sqlite3")
    create_db_if_not_exists(dpd_db_path)

    db_session = get_db_session(dpd_db_path)

    # add_roots(db_session)
    # add_words(db_session)

    # roots: List[PaliRoot] = db_session.query(PaliRoot).filter_by(root = "√kar 2").all()

    # if len(roots) > 0:
    #     for i in roots:
    #         print(f"{i.root} -- {i.root_meaning}")

    # kar_make = db_session \
    #     .query(PaliRoot) \
    #     .filter(and_(
    #         PaliRoot.root == "√kar 1",
    #         PaliRoot.root_meaning == "do, make")) \
    #     .first()

    # if kar_make is not None:
    #     for i in kar_make.pali_words:
    #         print(f"{i.pali1} -- {i.meaning1}")

    # Get all PaliWords
    words = db_session.query(PaliWord).all()
    for i in words:
        if i.pos == "adj":
            if i.pali_root is not None:
                print(f"{i.pali1}, {i.pos}: {i.meaning1} {i.pali_root.root} {i.pali_root.root_group} ({i.pali_root.root_meaning})")
        # # Use .pali_root to access the root's properties.
        # if i.pali_root is not None:
        #     print(f"    Root: {i.pali_root.root}")
        #     print(f"    Root meaning: {i.pali_root.root_meaning}")

    db_session.close()

if __name__ == "__main__":
    main()
