#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from rich import print
from sqlalchemy import outerjoin

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Sinhala
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_title
from tools.tic_toc import tic, toc
from sqlalchemy.orm import joinedload


def test_relationship():
    tic()
    p_green_title("relationship")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    dict = {}
    for counter, i in enumerate(db):
        dict[i.si_lemma] = i.si.si_meaning
        if counter % 10000 == 0:
            p_counter(counter, len(db), i.lemma_1)
        if counter == 40000:
            break
    print(len(dict))
    toc()

def test_outerjoin():
    tic()
    p_green_title("outerjoin")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).outerjoin(Sinhala, DpdHeadwords.id == Sinhala.id).all()
    dict = {}
    for counter, i in enumerate(db):
        dict[i.si_lemma] = i.si.si_meaning
        if counter % 10000 == 0:
            p_counter(counter, len(db), i.lemma_1)
        if counter == 40000:
            break
    print(len(dict))
    toc()


def test_joinedload():
    tic()
    p_green_title("joinedload")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).options(joinedload(DpdHeadwords.si)).all()
    dict = {}
    for counter, i in enumerate(db):
        dict[i.si_lemma] = i.si.si_meaning
        if counter % 10000 == 0:
            p_counter(counter, len(db), i.lemma_1)
        if counter == 40000:
            break
    print(len(dict))
    toc()


if __name__ == "__main__":
    test_relationship()
    test_outerjoin()
    test_joinedload()
