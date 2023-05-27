# json_vs_split_test.py

import json
from rich import print
from db.models import PaliWord, DerivedData
from db.get_db_session import get_db_session
from tools.tic_toc import bip, bop

db_session = get_db_session("dpd.db")


def json_paliword_test():
    db_query = db_session.query(PaliWord).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = json.loads(i.dd.inflections)
        all_inflections += inflections
    print(f"{'paliword > json.loads':<30} {len(all_inflections):>10} {bop()}")


def json_dd_test():
    db_query = db_session.query(DerivedData).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = json.loads(i.inflections)
        all_inflections += inflections
    print(f"{'deriveddata > json.loads':<30} {len(all_inflections):>10} {bop()}")


def split_paliword_test():
    db_query = db_session.query(PaliWord).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = i.dd.inflections.split(",")
        all_inflections += inflections
    print(f"{'paliword > split':<30} {len(all_inflections):>10} {bop()}")


def split_dd_test():
    db_query = db_session.query(DerivedData).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = i.inflections.split(",")
        all_inflections += inflections
    print(f"{'deriveddata > split':<30} {len(all_inflections):>10} {bop()}")


def list_dd_test():
    db_query = db_session.query(DerivedData).all()
    bip()
    all_inflections = []
    for i in db_query:
        inflections = i.inflections_list
        all_inflections += inflections
    print(f"{'deriveddata > list':<30} {len(all_inflections):>10} {bop()}")


def html_paliword_test():
    
    db_query = db_session.query(PaliWord).all()
    bip()
    all_tables = []
    for i in db_query:
        html_table = i.dd.html_table
        all_tables += [html_table]
    print(f"{'paliword > html':<30} {len(all_tables):>10} {bop()}")


def html_dd_test():
    
    db_query = db_session.query(DerivedData).all()
    bip()
    all_tables = []
    for i in db_query:
        html_table = i.html_table
        all_tables += [html_table]
    print(f"{'paliword > html':<30} {len(all_tables):>10} {bop()}")


def zip_test():

    pw = db_session.query(PaliWord).all()
    dd = db_session.query(DerivedData).all()

    bip()

    all_inflections = []
    for p, d in zip(pw, dd):
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
