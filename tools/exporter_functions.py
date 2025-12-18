from sqlalchemy.orm import object_session

from typing import List

from db.models import DpdHeadword, FamilyIdiom
from db.models import FamilyCompound
from db.models import FamilySet

from tools.paths import ProjectPaths

pth = ProjectPaths()


def get_family_compounds(i: DpdHeadword) -> List[FamilyCompound]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    if i.family_compound:
        fc = (
            db_session.query(FamilyCompound)
            .filter(FamilyCompound.compound_family.in_(i.family_compound_list))
            .all()
        )

        # sort by order of the  family compound list
        word_order = i.family_compound_list
        fc = sorted(fc, key=lambda x: word_order.index(x.compound_family))

    else:
        fc = (
            db_session.query(FamilyCompound)
            .filter(FamilyCompound.compound_family == i.lemma_clean)
            .all()
        )

    # Make sure it's not a lazy-loaded iterable.
    fc = list(fc)

    return fc


def get_family_idioms(i: DpdHeadword) -> List[FamilyIdiom]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    if i.family_idioms:
        fi = (
            db_session.query(FamilyIdiom)
            .filter(FamilyIdiom.idiom.in_(i.family_idioms_list))
            .all()
        )

        # sort by order of the  family compound list
        word_order = i.family_idioms_list
        fi = sorted(fi, key=lambda x: word_order.index(x.idiom))
    else:
        fi = (
            db_session.query(FamilyIdiom)
            .filter(FamilyIdiom.idiom == i.lemma_clean)
            .all()
        )

    # Make sure it's not a lazy-loaded iterable.
    fi = list(fi)

    return fi


def get_family_set(i: DpdHeadword) -> List[FamilySet]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    fs = db_session.query(FamilySet).filter(FamilySet.set.in_(i.family_set_list)).all()

    # sort by order of the  family set list
    word_order = i.family_set_list
    fs = sorted(fs, key=lambda x: word_order.index(x.set))

    # Make sure it's not a lazy-loaded iterable.
    fs = list(fs)

    return fs
