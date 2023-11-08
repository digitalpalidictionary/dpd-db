from db.get_db_session import get_db_session
from db.models import PaliRoot, PaliWord
from tools.paths import ProjectPaths
from tools.tic_toc import bip, bop
from rich import print

PTH = ProjectPaths()
db_session = get_db_session(PTH.dpd_db_path)


def property_method():
    bip()
    print("property_method")
    root_count: dict = {}
    roots_db = db_session.query(
        PaliRoot
        ).all()

    for i in roots_db:
        root_count[i.root] = i.root_count
    return bop(), len(root_count)


def dict_method():
    bip()
    print("dict_method")
    root_count: dict = {}
    roots_db = db_session.query(
        PaliRoot
    ).all()

    for i in roots_db:
        root_count[i.root] = db_session.query(
            PaliWord
        ).filter(
            PaliWord.root_key == i.root
        ).count()

    return bop(), len(root_count)


# print(property_method())
# print(dict_method())

db = db_session.query(
    PaliWord
).all()


def root_key():
    bip()
    for counter, i in enumerate(db):

        if counter < 1000:
            if i.root_key:
                print(i.pali_1, i.root_key, i.root_count)
    return bop()


def test_family_list():
    roots_db = db_session.query(
        PaliRoot
    ).all()
    for i in roots_db:
        print(i.root, i.root_family_list)


test_family_list()
