# json_vs_split_test.py

import json
from rich import print
from db.models import DpdHeadword
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from tools.tic_toc import bip, bop

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def json_paliword_test():
    db_query = db_session.query(DpdHeadword).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = json.loads(i.inflections)
        all_inflections += inflections
    print(f"{'paliword > json.loads':<30} {len(all_inflections):>10} {bop()}")


def json_dd_test():
    db_query = db_session.query(DpdHeadword).all()
    bip()
    all_inflections = []
    for i in db_query:
        if i.inflections is None:
            continue
        inflections = json.loads(i.inflections)
        all_inflections += inflections
    print(f"{'deriveddata > json.loads':<30} {len(all_inflections):>10} {bop()}")


def split_paliword_test():
    db_query = db_session.query(DpdHeadword).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = i.inflections.split(",")
        all_inflections += inflections
    print(f"{'paliword > split':<30} {len(all_inflections):>10} {bop()}")


def split_dd_test():
    db_query = db_session.query(DpdHeadword).all()
    bip()
    all_inflections = []
    for i in db_query:
        if i.inflections is None:
            continue
        inflections = i.inflections.split(",")
        all_inflections += inflections
    print(f"{'deriveddata > split':<30} {len(all_inflections):>10} {bop()}")


def list_dd_test():
    db_query = db_session.query(DpdHeadword).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = i.inflections_list
        all_inflections += inflections
    print(f"{'deriveddata > list':<30} {len(all_inflections):>10} {bop()}")


def html_paliword_test():
    db_query = db_session.query(DpdHeadword).all()
    bip()
    all_tables = []
    for i in db_query:
        html_table = i.html_table
        all_tables += [html_table]
    print(f"{'paliword > html':<30} {len(all_tables):>10} {bop()}")


def html_dd_test():
    db_query = db_session.query(DpdHeadword).all()
    bip()
    all_tables = []
    for i in db_query:
        html_table = i.html_table
        all_tables += [html_table]
    print(f"{'paliword > html':<30} {len(all_tables):>10} {bop()}")


def zip_test():
    pw = db_session.query(DpdHeadword).all()
    dd = db_session.query(DpdHeadword).all()

    bip()

    all_inflections = []
    for __p__, d in zip(pw, dd):
        if d.inflections is None:
            continue
        inflections = d.inflections.split(",")
        all_inflections += inflections
    print(f"{'zip > split':<30} {len(all_inflections):>10} {bop()}")


json_paliword_test()
split_paliword_test()
json_dd_test()
split_dd_test()
list_dd_test()
# html_paliword_test()
# html_dd_test()
zip_test()
print()


# end result:
# if you want speed: dd.inflections.split(",")
# if you want speed and ease: dd.inflections_list
# if you want the headwords: for i, j in zip(pali word, derived data)
# if you want 10 times slower: i.dd.inflections
