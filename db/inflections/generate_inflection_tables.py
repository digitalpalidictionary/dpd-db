#!/usr/bin/env python3

"""Generate all inflection tables and lists and save to database."""

import re
import json
import pickle

from rich import print
from typing import List, Dict, Tuple

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, InflectionTemplates

from tools.configger import config_test, config_update
from tools.tic_toc import tic, toc
from tools.pos import CONJUGATIONS
from tools.pos import DECLENSIONS
from tools.superscripter import superscripter_uni
from tools.paths import ProjectPaths


pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
dpd_db = db_session.query(DpdHeadwords).all()

changed_templates: list = []
changed_headwords: list = []

# !!! how is all_tipitaka_words getting generated?

with open(pth.all_tipitaka_words_path, "rb") as f:
    all_tipitaka_words: set = pickle.load(f)


def main():
    """run it."""
    tic()
    print("[bright_yellow]generate inflection lists and html tables")

    # check config
    if (
        config_test("regenerate", "inflections", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
    ):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False

    if regenerate_all is not True:
        test_changes()

    print("[green]generating html tables and lists")
    add_to_db = []
    for i in dpd_db:

        test1 = i.lemma_1 in changed_headwords
        test2 = i.pattern in changed_templates
        test3 = regenerate_all is True

        if test1 or test2 or test3:

            # regenerate is true then delete the whole table
            # regenerate is false then just delete the row
            # pattern != "" then add html table and list
            # stem contains "!" then add table and clean headword
            # pattern == "" then no table, just add clean headword

            if regenerate_all:
                pass
                # FIXME derived data table no longer exists!
                # db_session.execute(DerivedData.__table__.delete()) # type: ignore

            if i.pattern:
                html, inflections_list = generate_inflection_table(i)
                
                i.inflections = ",".join(inflections_list)
                i.inflections_html = html

                if "!" in i.stem:
                    i.inflections = i.lemma_clean
                    i.inflections_html = html
            else:
                i.inflections = i.lemma_clean



    db_session.commit()

    print("[green]adding to db")

    for row in add_to_db:
        db_session.add(row)

    with open(pth.changed_headwords_path, "wb") as f:
        pickle.dump(changed_headwords, f)

    with open(pth.template_changed_path, "wb") as f:
        pickle.dump(changed_templates, f)

    # # !!! find all unused patterns !!!

    if config_test("regenerate", "inflections", "yes"):
        config_update("regenerate", "inflections", "no")

    db_session.commit()
    db_session.close()
    toc()


def test_inflection_template_changed():
    """test if the inflection template has changes since the last run"""

    try:
        with open(pth.inflection_templates_pickle_path, "rb") as f:
            old_templates: List[InflectionTemplates] = pickle.load(f)
    except Exception:
        old_templates = []
    new_templates = db_session.query(InflectionTemplates).all()

    print("[green]testing for changed templates")
    for new_template in new_templates:
        for old_template in old_templates:
            if new_template.pattern == old_template.pattern:
                if new_template.data != old_template.data:
                    changed_templates.append(new_template.pattern)
    if changed_templates:
        print(f"	[red]{changed_templates}")

    print("[green]testing for added patterns")
    old_patterns: set = {table.pattern for table in old_templates}
    new_patterns: set = {table.pattern for table in new_templates}

    added_patterns: list = [
        table.pattern for table in new_templates
        if table.pattern not in old_patterns]

    if added_patterns != []:
        print(f"\t[red]{added_patterns}")
        changed_templates.extend(added_patterns)

    print("[green]testing for deleted patterns")
    deleted_patterns = [
        table.pattern for table in old_templates
        if table.pattern not in new_patterns]

    if deleted_patterns != []:
        print(f"\t[red]{deleted_patterns}")

    print("[green]testing for changed like")
    old_like = {table.like for table in old_templates}
    changed_like = [
        table.pattern for table in new_templates if table.like not in old_like]

    if changed_like != []:
        print(f"\t[red]{changed_like}")
        changed_templates.extend(changed_like)

    def save_pickle() -> None:
        tables = db_session.query(InflectionTemplates).all()
        with open(pth.inflection_templates_pickle_path, "wb") as f:
            pickle.dump(tables, f)

    save_pickle()


def test_missing_stem() -> None:
    """test for missing stem in db"""
    print("[green]testing for missing stem")

    for i in dpd_db:
        if not i.stem:
            print(
                f"\t[red]{i.lemma_1} {i.pos} has a missing stem.", end=" ")
            new_stem = input("what is the new stem? ")
            i.stem = new_stem
    db_session.commit()


def test_missing_pattern() -> None:
    """test for missing pattern in db"""
    print("[green]testing for missing pattern")

    for i in dpd_db:
        if i.stem != "-" and not i.pattern:
            print(f"\t[red]{i.lemma_1} {i.pos} has a missing pattern.", end=" ")
            new_pattern = input("what is the new pattern? ")
            i.pattern = new_pattern
    db_session.commit()


def test_wrong_pattern() -> None:
    """test if pattern exists in inflection templates"""
    print("[green]testing for wrong patterns")

    tables = db_session.query(InflectionTemplates).all()
    pattern_list: list = [table.pattern for table in tables]

    wrong_pattern_db = db_session.query(DpdHeadwords).filter(
        DpdHeadwords.pattern.notin_(pattern_list)).filter(
            DpdHeadwords.pattern != "").all()

    for i in wrong_pattern_db:
        print(f"\t[red]{i.lemma_1} {i.pos} has the wrong pattern.", end=" ")

        new_pattern = ""
        while new_pattern not in pattern_list:
            new_pattern = input("what is the new pattern? ")
            i.pattern = new_pattern

    db_session.commit()


def test_changes_in_stem_pattern() -> None:
    """test for changes in stem and pattern since last run"""
    print("[green]testing for changes in stem and pattern")

    try:
        with open(pth.headword_stem_pattern_dict_path, "rb") as f:
            old_dict: dict = pickle.load(f)
    except FileNotFoundError:
        old_dict = {}

    new_dict: Dict[str, Dict] = {}
    for i in dpd_db:
        new_dict[i.lemma_1] = {
            "stem": i.stem, "pattern": i.pattern}

    for headword, value in new_dict.items():
        if value != old_dict.get(headword, None):
            print(f"\t[red]{headword}")
            changed_headwords.append(headword)

    def save_pickle() -> None:
        headword_stem_pattern_dict: Dict[str, Dict] = {}
        for i in dpd_db:
            headword_stem_pattern_dict[i.lemma_1] = {
                "stem": i.stem, "pattern": i.pattern}

        with open(pth.headword_stem_pattern_dict_path, "wb") as f:
            pickle.dump(headword_stem_pattern_dict, f)

    save_pickle()


def test_missing_inflection_list_html() -> None:
    """test for missing inflections in dpd_headwords table"""

    print("[green]testing for missing inflection list and html tables")

    for i in dpd_db:
        if not i.inflections:
            print(f"\t[red]{i.lemma_1}")
            changed_headwords.append(i.lemma_1)


def test_changes() -> None:
    """run all the tests"""
    test_inflection_template_changed()
    test_missing_stem()
    test_missing_pattern()
    test_wrong_pattern()
    test_changes_in_stem_pattern()
    test_missing_inflection_list_html()


def generate_inflection_table(i: DpdHeadwords) -> Tuple[str, list]:
    """generate the inflection table based on stem + pattern and template"""

    if i.it is None or i.it.data is None:
        return "", []

    table_data = json.loads(i.it.data)
    inflections_list: list = [i.lemma_clean]

    # heading
    html: str = "<p class='heading'>"
    html += f"<b>{superscripter_uni(i.lemma_1)}</b> is <b>{i.pattern}</b> "
    if i.it.like != "irreg":
        if i.pos in CONJUGATIONS:
            html += "conjugation "
        elif i.pos in DECLENSIONS:
            html += "declension "
        html += f"(like <b>{i.it.like})</b>"
    else:
        if i.pos in CONJUGATIONS:
            html += "conjugation "
        if i.pos in DECLENSIONS:
            html += "declension "
        html += "(irregular)"
    html += "</p>"

    html += "<table class='inflection'>"
    stem = re.sub(r"\!|\*", "", i.stem)

    # data is a nest of lists
    # list[] table
    # list[[]] row
    # list[[[]]] cell
    # row 0 is the top header
    # column 0 is the grammar header
    # odd rows > 0 are inflections
    # even rows > 0 are grammar info

    for row in enumerate(table_data):
        row_number: int = row[0]
        row_data: List[list] = row[1]
        html += "<tr>"
        for column in enumerate(row_data):
            column_number: int = column[0]
            cell_data: List = column[1]
            if row_number == 0:
                if column_number == 0:
                    html += "<th></th>"
                if column_number % 2 == 1:
                    html += f"<th>{cell_data[0]}</th>"
            elif row_number > 0:
                if column_number == 0:
                    html += f"<th>{cell_data[0]}</th>"
                elif column_number % 2 == 1 and column_number > 0:
                    title: str = [row_data[column_number + 1]][0][0]

                    for inflection in cell_data:
                        if not inflection:
                            html += f"<td title='{title}'></td>"
                        else:
                            word_clean = f"{stem}{inflection}"
                            if word_clean in all_tipitaka_words:
                                word = f"{stem}<b>{inflection}</b>"
                            else:
                                word = f"<span class='gray'>{stem}<b>{inflection}</b></span>"

                            if len(cell_data) == 1:
                                html += f"<td title='{title}'>{word}</td>"
                            else:
                                if inflection == cell_data[0]:
                                    html += f"<td title='{title}'>{word}<br>"
                                elif inflection != cell_data[-1]:
                                    html += f"{word}<br>"
                                else:
                                    html += f"{word}</td>"
                            if word_clean not in inflections_list:
                                inflections_list.append(word_clean)

        html += "</tr>"
    html += "</table>"

    return html, inflections_list


if __name__ == "__main__":
    main()


# sanity tests
# ---------------------------
# add a word
# delete a word
# change a stem
# change a pattern
# add a template
# delete a template
# change a template
# √ check stem contains "!" only 1 inflection
# check no pattern = no table
