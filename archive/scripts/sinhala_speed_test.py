#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Sinhala
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from sqlalchemy.orm import joinedload


def test_relationship():
    pr.tic()
    pr.green_title("relationship")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    dict = {}
    for counter, i in enumerate(db):
        dict[i.lemma_si] = i.si.meaning_si
        if counter % 10000 == 0:
            pr.counter(counter, len(db), i.lemma_1)
        if counter == 40000:
            break
    print(len(dict))
    pr.toc()


def test_outerjoin():
    pr.tic()
    pr.green_title("outerjoin")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = (
        db_session.query(DpdHeadword)
        .outerjoin(Sinhala, DpdHeadword.id == Sinhala.id)
        .all()
    )
    dict = {}
    for counter, i in enumerate(db):
        dict[i.lemma_si] = i.si.meaning_si
        if counter % 10000 == 0:
            pr.counter(counter, len(db), i.lemma_1)
        if counter == 40000:
            break
    print(len(dict))
    pr.toc()


def test_joinedload():
    pr.tic()
    pr.green_title("joinedload")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.si)).all()
    dict = {}
    for counter, i in enumerate(db):
        dict[i.lemma_si] = i.si.meaning_si
        if counter % 10000 == 0:
            pr.counter(counter, len(db), i.lemma_1)
        if counter == 40000:
            break
    print(len(dict))
    pr.toc()


if __name__ == "__main__":
    test_relationship()
    test_outerjoin()
    test_joinedload()
