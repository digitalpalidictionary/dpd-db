# !/usr/bin/env python3

import re
import pickle

from rich import print
from db.models import DpdHeadword
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

pos_list = [
    'abbrev', 'abs', 'adj', 'aor', 'card', 'cond', 'cs', 'fem', 'fut', 'ger',
    'idiom', 'imp', 'imperf', 'ind', 'inf', 'letter', 'masc', 'nt', 'opt',
    'ordin', 'perf', 'pp', 'pr', 'prefix', 'pron', 'prp', 'ptp', 'root',
    'sandhi', 'suffix', 'var', 've']


def family_root_contains_plus():
    print("[green]family root contains plus")

    filtered_db = db_session.query(DpdHeadword).filter(
        DpdHeadword.family_root.contains("+")).all()

    for i in filtered_db:
        i.family_root = re.sub(r" \+ ", " ", str(i.family_root))
        db_session.commit()


def family_compound_contains_plus():
    print("[green]family compound contains plus")
    filtered_db = db_session.query(DpdHeadword).filter(
        DpdHeadword.family_compound.contains("+")).all()

    for i in filtered_db:
        i.family_compound = re.sub(r" \+ ", " ", str(i.family_compound))
        db_session.commit()


def family_root_missing():
    print("[green]family root missing")
    filtered_db = db_session.query(DpdHeadword).filter(
        DpdHeadword.family_root == "",
        DpdHeadword.root_key
    ).all()

    if len(filtered_db) > 0:
        print("[green]family_root missing ")
        for i in filtered_db:
            print(f"[bright_red]\t{i}")
            input()
            family_root_missing()


def problem_patterns():
    print("[green]problem patterns")
    with open(
            "../inflection generator/output/InflectionTemplatess dict",
            "rb") as p:
        inflection_templates_dict = pickle.load(p)
    patterns = inflection_templates_dict.keys()

    filtered_db = db_session.query(DpdHeadword).filter(
        DpdHeadword.pattern,
        DpdHeadword.pattern.notin_(patterns)
        ).all()

    if len(filtered_db) > 0:
        for i in filtered_db:
            print(f"[bright_red]\t{i.id} {i.lemma_1} {i.pattern}")
        input()
        problem_patterns()


def wrong_pos():
    print("[green]wrong pos")

    filtered_db = db_session.query(DpdHeadword).filter(
        DpdHeadword.pos.notin_(pos_list)).all()
    if len(filtered_db) > 0:
        for i in filtered_db:
            print(f"[bright_red]\t{i.id} {i.lemma_1} {i.pos}")
        input()
        wrong_pos()


def main():
    print("[bright_yellow] testing for common errors")
    family_root_contains_plus()
    family_compound_contains_plus()
    family_root_missing()
    problem_patterns()
    wrong_pos()
    # test for pos ≠ pattern
    # <br> in family 2
    # missing abbreviations in help file
    # test_for_errors_in_sandhi_manual_correct


if __name__ == "__main__":
    main()
