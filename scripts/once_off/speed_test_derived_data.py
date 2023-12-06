#!/usr/bin/env python3

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, DerivedData, FamilyRoot
from tools.paths import ProjectPaths
from tools.tic_toc import bip, bop


pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def join_method():
    bip()
    dpd_db = db_session.query(
        PaliWord, DerivedData, FamilyRoot
    ).outerjoin(
        DerivedData,
        PaliWord.id == DerivedData.id
    ).outerjoin(
        FamilyRoot,
        PaliWord.root_key + " " + PaliWord.family_root == FamilyRoot.root_family
    ).all()

    for counter, (i, dd, fr) in enumerate(dpd_db):

        pali = i.pali_1

        if i.meaning_1:
            meaning = i.meaning_1
        else:
            meaning = i.meaning_2
        inflections = dd.inflections
        if fr is not None:
            root_family = fr.root_family
        else:
            root_family = ""

        if counter % 1000 == 0:
            print(counter, pali, meaning, inflections, root_family)

    return bop()


def search_method():
    bip()
    dpd_db = db_session.query(
        PaliWord).all()

    for counter, i in enumerate(dpd_db):

        pali = i.pali_1

        if i.meaning_1:
            meaning = i.meaning_1
        else:
            meaning = i.meaning_2

        dd = db_session.query(
            DerivedData
            ).filter(
                i.id == DerivedData.id
            ).first()
        inflections = dd.inflections

        fr = db_session.query(
            FamilyRoot
            ).filter(
                f"{i.root_key} {i.family_root}" == FamilyRoot.root_family
            ).first()

        root_family = ""
        if fr is not None:
            root_family = fr.root_family

        if counter % 1000 == 0:
            print(counter, pali, meaning, inflections, root_family)

    return bop()


join = join_method()
search = search_method()
print(f"{join=}")
print(f"{search=}")
