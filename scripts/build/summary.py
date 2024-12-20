#!/usr/bin/env python3

"""Compile a summary of latest dictionary data to accompany a release."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, Lookup
from tools.configger import config_test
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.uposatha_day import uposatha_today, write_uposatha_count, read_uposatha_count
from tools.printer import p_title, p_green, p_green_title, p_yes


class GlobalVars():
    def __init__(self) -> None:
        p_green("preparing data")

        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db = self.db_session.query(DpdHeadword).all()
        self.roots_db = self.db_session.query(DpdRoot).all()
        self.deconstructor_db = self.db_session.query(Lookup) \
            .filter(Lookup.deconstructor != "") \
            .all()
        
        self.last_id = read_uposatha_count()
        self.new_words_db = self.db_session.query(DpdHeadword) \
            .filter(DpdHeadword.id > self.last_id) \
            .all()

        self.root_families: dict[str, int]
        self.line_1: str
        self.line_2: str
        self.line_3: str
        self.line_4: str
        self.line_5: str
        self.line_6: str
        self.line_7: str
        self.summary: str
        
        p_yes("ok")


def dpd_size(g: GlobalVars):
    """Summary of dpd_headwords table"""

    total_headwords = len(g.dpd_db)
    total_complete = 0
    total_partially_complete = 0
    total_incomplete = 0
    root_families: dict[str, int] = {}
    total_data = 0

    columns = DpdHeadword.__table__.columns
    column_names = [c.name for c in columns]
    exceptions = ["id", "created_at", "updated_at"]

    for i in g.dpd_db:
        if i.meaning_1:
            if i.example_1:
                total_complete += 1
            else:
                total_partially_complete += 1
        else:
            total_incomplete += 1
        if i.root_key:
            subfamily = f"{i.root_key} {i.family_root}"
            if subfamily in root_families:
                root_families[f"{i.root_key} {i.family_root}"] += 1
            else:
                root_families[f"{i.root_key} {i.family_root}"] = 1

        for column in column_names:
            if column not in exceptions:
                cell_value = getattr(i, column)
                if cell_value:
                    total_data += 1

    line1 = "- "
    line1 += f"{total_headwords:_} headwords, "
    line1 += f"{total_complete:_} complete, "
    line1 += f"{total_partially_complete:_} partially complete, "
    line1 += f"{total_incomplete:_} incomplete entries"
    line1 = line1.replace("_", " ")

    line5 = f"- {total_data:_} cells of Pāḷi word data"
    line5 = line5.replace("_", " ")

    g.line_1 = line1
    g.line_5 = line5
    g.root_families = root_families


def root_size(g: GlobalVars):
    """Summary of root families."""

    total_roots = len(g.roots_db)
    total_root_families = len(g.root_families)
    total_derived_from_roots = 0
    for family in g.root_families:
        total_derived_from_roots += g.root_families[family]

    line2 = "- "
    line2 += f"{total_roots:_} roots, "
    line2 += f"{total_root_families:_} root families, "
    line2 += f"{total_derived_from_roots:_} words derived from roots"
    line2 = line2.replace("_", " ")

    g.line_2 = line2


def deconstructor_size(g: GlobalVars):
    """Summary of deconstructor"""

    total_deconstructions = len(g.deconstructor_db)
    line3 = f"- {total_deconstructions:_} deconstructed compounds"
    line3 = line3.replace("_", " ")
    
    g.line_3 = line3


def inflection_size(g: GlobalVars):
    """"Summarize inflections."""

    total_inflections = 0
    all_inflection_set = set()

    for i in g.dpd_db:
        inflections = i.inflections_list
        total_inflections += len(inflections)
        all_inflection_set.update(inflections)

    line4 = f"- {total_inflections:_} unique inflected forms recognised"
    line4 = line4.replace("_", " ")

    g.line_4 = line4


def root_data(g: GlobalVars):
    """Summarize dpd_roots table"""
    
    columns = DpdRoot.__table__.columns
    column_names = [c.name for c in columns]
    exceptions = ["root_info", "root_matrix", "created_at", "updated_at"]
    total_roots_data = 0

    for i in g.roots_db:
        for column in column_names:
            if column not in exceptions:
                cell_value = getattr(i, column)
                if cell_value:
                    total_roots_data += 1

    line6 = f"- {total_roots_data:_} cells of Pāḷi root data"
    line6 = line6.replace("_", " ")

    g.line_6 = line6


def new_words(g: GlobalVars):
    """New words since the last uposatha day."""

    new_words = [i.lemma_1 for i in g.new_words_db]
    new_words = sorted(new_words, key=pali_sort_key)
    new_words_string = "**new words include:** "
    for nw in new_words:
        # comma on all words except the last
        if nw != new_words[-1]:
            new_words_string += f"{nw}, "
        else: 
            new_words_string += f"{nw} "
    new_words_string += f"[{len(new_words)}]"

    g.line_7 = new_words_string


def make_summary_string(g: GlobalVars):
    """Make a summary string for printing and saving to .md file."""

    g.summary = f"""
**Change-log**:
{g.line_1}
{g.line_2}
{g.line_3}
{g.line_4}
{g.line_5}
{g.line_6}
- 100% dictionary recognition in the early texts
- xyz
- numerous additions and corrections based on user feedback

{g.line_7}
"""


def main():
    tic()
    p_title("making summary")

    if not config_test("exporter", "summary", "yes"):
        p_green_title("disabled in config.ini")
        toc()

    else:
        g = GlobalVars()
        dpd_size(g)
        root_size(g)
        deconstructor_size(g)
        inflection_size(g)
        root_data(g)
        new_words(g)
        make_summary_string(g)
        
        with open(g.pth.summary_md_path, "w") as f:
            f.write(g.summary)
        
        p_yes("ok")

        if uposatha_today():
            p_green("updating uposatha count")
            last_id = g.dpd_db[-1].id
            write_uposatha_count(last_id)
            p_yes(last_id)
        
        toc()

        print(g.summary)

if __name__ == "__main__":
    main()
