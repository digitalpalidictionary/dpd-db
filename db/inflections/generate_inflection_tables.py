#!/usr/bin/env python3

"""Generate all inflection tables and lists and save to database."""

import re
import json
import pickle

from db.db_helpers import get_db_session
from db.models import DpdHeadword, InflectionTemplates, DbInfo

from tools.configger import config_test, config_update
from tools.tic_toc import tic, toc
from tools.pos import CONJUGATIONS
from tools.pos import DECLENSIONS
from tools.superscripter import superscripter_uni
from tools.paths import ProjectPaths
from tools.printer import p_title, p_green, p_red, p_yes, p_green_title


class GlobalVars():
    """Globally used variables."""

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()
    
    inflection_templates_db = tables = db_session.query(InflectionTemplates).all()
    inflection_patterns: list[str] = [t.pattern for t in inflection_templates_db]

    wrong_pattern_db = db_session.query(DpdHeadword) \
        .filter(DpdHeadword.pattern.notin_(inflection_patterns)) \
        .filter(DpdHeadword.pattern != "") \
        .all()

    changed_templates_db: DbInfo = db_session \
        .query(DbInfo) \
        .filter_by(key="changed_templates_list") \
        .first()
    
    changed_templates = changed_templates_db.value_unpack
    changed_headwords: list = []
    updated_counter = 0

    # all tipitaka words
    with open(pth.all_tipitaka_words_path, "rb") as f:
        all_tipitaka_words: set = pickle.load(f)

    # regenerate all
    if (
        config_test("regenerate", "inflections", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
    ):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False

    # current headword
    i: DpdHeadword

    # generated data
    inflections_html: str
    inflections_list: list[str]


def test_missing_stem(g: GlobalVars) -> None:
    """Test for missing stem in db."""

    p_green("testing for missing stem")
    for i in g.dpd_db:
        if not i.stem:
            p_red(f"{i.lemma_1} {i.pos} has a missing stem.")
            p_green_title("what is the new stem?")
            new_stem = input()
            i.stem = new_stem
            g.db_session.commit()
    p_yes("ok")


def test_missing_pattern(g: GlobalVars) -> None:
    """Test for missing pattern in db."""

    p_green("testing for missing pattern")
    for i in g.dpd_db:
        if i.stem != "-" and not i.pattern:
            p_red(f"{i.lemma_1} {i.pos} has a missing pattern.")
            p_green_title("what is the new pattern?")
            new_pattern = input()
            i.pattern = new_pattern
            g.db_session.commit()
    p_yes("ok")


def test_wrong_pattern(g: GlobalVars) -> None:
    """Test if pattern exists in inflection templates."""
    
    p_green("testing for wrong patterns")
    for i in g.wrong_pattern_db:
        p_red(f"{i.lemma_1} {i.pos} has the wrong pattern.")
        new_pattern = ""
        while new_pattern not in g.inflection_patterns:
            p_green_title("what is the new pattern?")
            new_pattern = input()
            i.pattern = new_pattern
            g.db_session.commit()
    p_yes("ok")


def test_changes_in_stem_pattern(g: GlobalVars) -> None:
    """Test for changes in stem and pattern since last run."""

    p_green_title("testing for changes in stem and pattern")
    try:
        with open(g.pth.headword_stem_pattern_dict_path, "rb") as f:
            old_dict: dict = pickle.load(f)
    except FileNotFoundError:
        old_dict = {}

    new_dict: dict[str, dict] = {}
    for i in g.dpd_db:
        new_dict[i.lemma_1] = {
            "stem": i.stem, "pattern": i.pattern}

    for headword, value in new_dict.items():
        if value != old_dict.get(headword, None):
            p_red(f"\t{headword}")
            g.changed_headwords.append(headword)

    def save_pickle() -> None:
        headword_stem_pattern_dict: dict[str, dict] = {}
        for i in g.dpd_db:
            headword_stem_pattern_dict[i.lemma_1] = {
                "stem": i.stem, "pattern": i.pattern}

        with open(g.pth.headword_stem_pattern_dict_path, "wb") as f:
            pickle.dump(headword_stem_pattern_dict, f)

    save_pickle()


def test_missing_inflection_list_html(g: GlobalVars) -> None:
    """Test for missing inflections in dpd_headwords table"""

    p_green_title("testing for missing inflection list and html tables")
    for i in g.dpd_db:
        if not i.inflections:
            p_red(f"\t{i.lemma_1}")
            g.changed_headwords.append(i.lemma_1)
    

def generate_inflection_table(g: GlobalVars):
    """Generate the inflection table based on stem + pattern and template"""

    i = g.i

    if i.it is None or i.it.data is None:
        p_red(f"ERROR: {i.id} {i.lemma_1} {i.pattern} does not exist")
        return "", []

    table_data = json.loads(i.it.data)
    g.inflections_list = [i.lemma_clean]

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
        row_data: list[list] = row[1]
        html += "<tr>"
        for column in enumerate(row_data):
            column_number: int = column[0]
            cell_data: list = column[1]
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
                            if word_clean in g.all_tipitaka_words:
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
                            if word_clean not in g.inflections_list:
                                g.inflections_list.append(word_clean)

        html += "</tr>"
    html += "</table>"

    g.inflections_html = html


def run_tests(g: GlobalVars):
    """Run all the tests."""

    test_missing_stem(g)
    test_missing_pattern(g)
    test_wrong_pattern(g)
    test_changes_in_stem_pattern(g)
    test_missing_inflection_list_html(g)


def process_inflection(g: GlobalVars):
    """Process inflection for each headword"""

    i = g.i

    test1 = i.lemma_1 in g.changed_headwords
    test2 = i.pattern in g.changed_templates
    test3 = g.regenerate_all is True

    if test1 or test2 or test3:
        if i.pattern:
            generate_inflection_table(g)

            if "!" in i.stem:
                # in this case the headword itself is inflected
                # add the html table and clean headword 
                i.inflections = i.lemma_clean
                i.inflections_html = g.inflections_html
            
            else:
                # in this case it's a normal headword
                # add the html table and inflections list
                i.inflections = ",".join(g.inflections_list)                
                i.inflections_html = g.inflections_html
        
        else:
            # in this case it's an indeclinable
            # don't add the html table, only the clean headword
            i.inflections = i.lemma_clean
        
        g.updated_counter += 1


def main():
    
    tic()
    p_title("generate inflection lists and html tables")
    g = GlobalVars()

    if g.regenerate_all is False:
        run_tests(g)
    else:
        test_wrong_pattern(g)
    
    p_green("generating html tables and lists")
    for g.i in g.dpd_db:
        process_inflection(g)
    p_yes(g.updated_counter)

    p_green("committing to db")
    g.db_session.commit()
    g.db_session.close()
    p_yes(g.updated_counter)

    with open(g.pth.changed_headwords_path, "wb") as f:
        pickle.dump(g.changed_headwords, f)

    if config_test("regenerate", "inflections", "yes"):
        config_update("regenerate", "inflections", "no")

    toc()


if __name__ == "__main__":
    main()

# FIXME how is all_tipitaka_words getting generated?


# tests
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
