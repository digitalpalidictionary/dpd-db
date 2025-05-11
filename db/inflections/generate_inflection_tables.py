#!/usr/bin/env python3

"""Generate all inflection tables and lists and save to database."""

import re
import json
import pickle
from typing import Optional, Set
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, InflectionTemplates, DbInfo

from tools.configger import config_test, config_update
from tools.printer import printer as pr
from tools.pos import CONJUGATIONS
from tools.pos import DECLENSIONS
from tools.superscripter import superscripter_uni
from tools.paths import ProjectPaths


class InflectionsManager:
    """Manage inflection generation."""

    def __init__(self) -> None:
        """Initialize the InflectionsManager."""
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.inflection_templates_db: list[InflectionTemplates] = self.db_session.query(
            InflectionTemplates
        ).all()
        self.inflection_patterns: list[str] = [
            t.pattern for t in self.inflection_templates_db
        ]
        self.wrong_pattern_db: list[DpdHeadword] = (
            self.db_session.query(DpdHeadword)
            .filter(DpdHeadword.pattern.notin_(self.inflection_patterns))
            .filter(DpdHeadword.pattern != "")
            .all()
        )
        self.changed_templates_db: Optional[DbInfo] = (
            self.db_session.query(DbInfo)
            .filter_by(key="changed_templates_list")
            .first()
        )
        self.changed_templates: list = []
        if self.changed_templates_db:
            self.changed_templates = self.changed_templates_db.value_unpack

        self.changed_headwords: list[str] = []
        self.updated_counter: int = 0
        self.inflections_html: str = ""
        self.inflections_list: list[str] = []

        with open(self.pth.all_tipitaka_words_path, "rb") as f:
            self.all_tipitaka_words: Set = pickle.load(f)

        self.regenerate_all: bool = config_test(
            "regenerate", "inflections", "yes"
        ) or config_test("regenerate", "db_rebuild", "yes")

    def test_missing_stem(self) -> None:
        """Test for missing stem in db."""
        pr.green("testing for missing stem")
        for i in self.dpd_db:
            if not i.stem:
                pr.red(f"{i.lemma_1} {i.pos} has a missing stem.")
                pr.green_title("what is the new stem?")
                new_stem = input()
                i.stem = new_stem
                self.db_session.commit()
        pr.yes("ok")

    def test_missing_pattern(self) -> None:
        """Test for missing pattern in db."""
        pr.green("testing for missing pattern")
        for i in self.dpd_db:
            if i.stem != "-" and not i.pattern:
                pr.red(f"{i.lemma_1} {i.pos} has a missing pattern.")
                pr.green_title("what is the new pattern?")
                new_pattern = input()
                i.pattern = new_pattern
                self.db_session.commit()
        pr.yes("ok")

    def test_wrong_pattern(self) -> None:
        """Test if pattern exists in inflection templates."""
        pr.green("testing for wrong patterns")
        for i in self.wrong_pattern_db:
            pr.red(f"{i.lemma_1} {i.pos} has the wrong pattern.")
            new_pattern = ""
            while new_pattern not in self.inflection_patterns:
                pr.green_title("what is the new pattern?")
                new_pattern = input()
                i.pattern = new_pattern
                self.db_session.commit()
        pr.yes("ok")

    def _save_pickle(self) -> None:
        """Save the current headword stem/pattern dict to a pickle file."""
        headword_stem_pattern_dict: dict[str, dict] = {}
        for i in self.dpd_db:
            headword_stem_pattern_dict[i.lemma_1] = {
                "stem": i.stem,
                "pattern": i.pattern,
            }
        with open(self.pth.headword_stem_pattern_dict_path, "wb") as f:
            pickle.dump(headword_stem_pattern_dict, f)

    def test_changes_in_stem_pattern(self) -> None:
        """Test for changes in stem and pattern since last run."""
        pr.green_title("testing for changes in stem and pattern")
        try:
            with open(self.pth.headword_stem_pattern_dict_path, "rb") as f:
                old_dict: dict = pickle.load(f)
        except FileNotFoundError:
            old_dict = {}

        new_dict: dict[str, dict] = {}
        for i in self.dpd_db:
            new_dict[i.lemma_1] = {"stem": i.stem, "pattern": i.pattern}

        for headword, value in new_dict.items():
            if value != old_dict.get(headword, None):
                pr.red(f"\t{headword}")
                self.changed_headwords.append(headword)

        self._save_pickle()

    def test_missing_inflection_list_html(self) -> None:
        """Test for missing inflections in dpd_headwords table"""
        pr.green_title("testing for missing inflection list and html tables")
        for i in self.dpd_db:
            if not i.inflections:
                pr.red(f"\t{i.lemma_1}")
                self.changed_headwords.append(i.lemma_1)

    def generate_inflection_table(self, i: DpdHeadword) -> None:
        """Generate the inflection table based on stem + pattern and template"""
        if i.it is None or i.it.data is None:
            pr.red(f"ERROR: {i.id} {i.lemma_1} {i.pattern} does not exist")
            self.inflections_html = ""
            self.inflections_list = []
            return

        # data is a nest of lists
        # list[] table
        # list[[]] row
        # list[[[]]] cell
        # row 0 is the top header
        # column 0 is the grammar header
        # odd rows > 0 are inflections
        # even rows > 0 are grammar info
        table_data = json.loads(i.it.data)
        current_inflections_list: list[str] = [i.lemma_clean]
        html: str = "<p class='heading'>"
        html += f"<b>{superscripter_uni(i.lemma_1)}</b> is <b>{i.pattern}</b> "
        if i.it.like != "irreg":
            if i.pos in CONJUGATIONS:
                html += "conjugation "
            elif i.pos in DECLENSIONS:
                html += "declension "
            html += f"(like <b>{i.it.like}</b>)"
        else:
            if i.pos in CONJUGATIONS:
                html += "conjugation "
            if i.pos in DECLENSIONS:
                html += "declension "
            html += "(irregular)"
        html += "</p>"

        html += "<table class='inflection'>"
        stem = re.sub(r"\!|\*", "", i.stem)

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
                                if word_clean in self.all_tipitaka_words:
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
                                if word_clean not in current_inflections_list:
                                    current_inflections_list.append(word_clean)

            html += "</tr>"
        html += "</table>"

        self.inflections_html = html
        self.inflections_list = current_inflections_list

    def run_tests(self) -> None:
        """Run all the tests."""
        self.test_missing_stem()
        self.test_missing_pattern()
        self.test_wrong_pattern()
        self.test_changes_in_stem_pattern()
        self.test_missing_inflection_list_html()

    def process_inflection(self, i: DpdHeadword) -> None:
        """Process inflection for a single headword"""
        test1 = i.lemma_1 in self.changed_headwords
        test2 = i.pattern in self.changed_templates
        test3 = self.regenerate_all

        if test1 or test2 or test3:
            if i.pattern:
                self.generate_inflection_table(i)

                if "!" in i.stem:
                    # in this case the headword itself is inflected
                    # add the html table and clean headword
                    i.inflections = i.lemma_clean
                    i.inflections_html = self.inflections_html
                else:
                    # in this case it's a normal headword
                    # add the html table and inflections list
                    i.inflections = ",".join(self.inflections_list)
                    i.inflections_html = self.inflections_html
            else:
                # in this case it's an indeclinable
                # don't add the html table, only the clean headword
                i.inflections = i.lemma_clean

            self.updated_counter += 1

    def process_all_inflections(self) -> None:
        """Process inflections for all headwords in the database."""
        pr.green("generating html tables and lists")
        initial_counter = self.updated_counter
        for i in self.dpd_db:
            self.process_inflection(i)
        pr.yes(self.updated_counter - initial_counter)

    def run(self) -> None:
        """Execute the entire inflection generation process."""
        pr.tic()
        pr.title("generate inflection lists and html tables")

        if not self.regenerate_all:
            self.run_tests()
        else:
            self.test_wrong_pattern()

        self.process_all_inflections()

        pr.green("committing to db")
        try:
            self.db_session.commit()
            pr.yes(self.updated_counter)
        except Exception as e:
            pr.red(f"Error committing to db: {e}")
            self.db_session.rollback()
        finally:
            self.db_session.close()

        pr.green("saving changed headwords list")
        try:
            with open(self.pth.changed_headwords_path, "wb") as f:
                pickle.dump(self.changed_headwords, f)
            pr.yes(len(self.changed_headwords))
        except Exception as e:
            pr.no(f"Error saving pickle file: {e}")

        if config_test("regenerate", "inflections", "yes"):
            config_update("regenerate", "inflections", "no")

        pr.toc()


def main():
    """Initialize and run the inflection generation process."""
    manager = InflectionsManager()
    manager.run()


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
