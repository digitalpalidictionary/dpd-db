#!/usr/bin/env python3

"""
Create all the data necessary for release notes and website changelog
1. Release preamble
2. Github Issues Closed
3. Dictionary data
4. New Words
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from github import Github
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, Lookup
from tools.configger import config_test
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.uposatha_day import UposathaManger


class GlobalVars:
    def __init__(self) -> None:
        pr.green("preparing data")

        self.pth: ProjectPaths = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db: List[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.roots_db: List[DpdRoot] = self.db_session.query(DpdRoot).all()
        self.deconstructor_db: List[Lookup] = (
            self.db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
        )

        uposatha_count = UposathaManger.read_uposatha_count()
        self.last_id: str = str(uposatha_count) if uposatha_count is not None else "0"

        self.new_words_db: List[DpdHeadword] = (
            self.db_session.query(DpdHeadword)
            .filter(DpdHeadword.id > int(self.last_id))
            .all()
        )

        self.github_issues: str
        self.date: str = datetime.today().strftime("%Y-%m-%d")

        self.root_families: Dict[str, int]
        self.line_1_headwords: str
        self.line_2_roots: str
        self.line_3_deconstructor: str
        self.line_4_inflections: str
        self.line_5_cell_of_pali_data: str
        self.line_6_cells_of_root_data: str
        self.new_words: str

        self.release_notes: str
        self.changelog: str

        pr.yes("ok")


def get_dpd_size(g: GlobalVars) -> None:
    """Summary of dpd_headwords table"""

    total_headwords: int = len(g.dpd_db)
    total_complete: int = 0
    total_partially_complete: int = 0
    total_incomplete: int = 0
    root_families: Dict[str, int] = {}
    total_data: int = 0

    columns = DpdHeadword.__table__.columns
    column_names: List[str] = [c.name for c in columns]
    exceptions: List[str] = ["id", "created_at", "updated_at"]

    for i in g.dpd_db:
        if i.meaning_1:
            if i.source_1:
                total_complete += 1
            else:
                total_partially_complete += 1
        else:
            total_incomplete += 1
        if i.root_key:
            subfamily: str = f"{i.root_key} {i.family_root}"
            if subfamily in root_families:
                root_families[f"{i.root_key} {i.family_root}"] += 1
            else:
                root_families[f"{i.root_key} {i.family_root}"] = 1

        for column in column_names:
            if column not in exceptions:
                cell_value: Optional[str] = getattr(i, column)
                if cell_value:
                    total_data += 1

    line1: str = ""
    line1 += f"{total_headwords:_} headwords, "
    line1 += f"{total_complete:_} complete, "
    line1 += f"{total_partially_complete:_} partially complete, "
    line1 += f"{total_incomplete:_} incomplete entries"
    line1 = line1.replace("_", " ")

    line5: str = f"{total_data:_} cells of Pāḷi word data"
    line5 = line5.replace("_", " ")

    g.line_1_headwords = line1
    g.line_5_cell_of_pali_data = line5
    g.root_families = root_families


def get_root_size(g: GlobalVars) -> None:
    """Summary of root families."""

    total_roots: int = len(g.roots_db)
    total_root_families: int = len(g.root_families)
    total_derived_from_roots: int = 0
    for family in g.root_families:
        total_derived_from_roots += g.root_families[family]

    line2: str = ""
    line2 += f"{total_roots:_} roots, "
    line2 += f"{total_root_families:_} root families, "
    line2 += f"{total_derived_from_roots:_} words derived from roots"
    line2 = line2.replace("_", " ")

    g.line_2_roots = line2


def get_deconstructor_size(g: GlobalVars) -> None:
    """Summary of deconstructor"""

    total_deconstructions: int = len(g.deconstructor_db)
    line3: str = f"{total_deconstructions:_} deconstructed compounds"
    line3 = line3.replace("_", " ")

    g.line_3_deconstructor = line3


def get_inflection_size(g: GlobalVars) -> None:
    """ "Summarize inflections."""

    total_inflections: int = 0
    all_inflection_set: set[str] = set()

    for i in g.dpd_db:
        inflections: List[str] = i.inflections_list
        total_inflections += len(inflections)
        all_inflection_set.update(inflections)

    line4: str = f"{len(all_inflection_set):_} unique inflected forms recognized"
    line4 = line4.replace("_", " ")

    g.line_4_inflections = line4


def get_root_data(g: GlobalVars) -> None:
    """Summarize dpd_roots table"""

    columns = DpdRoot.__table__.columns
    column_names: List[str] = [c.name for c in columns]
    exceptions: List[str] = ["root_info", "root_matrix", "created_at", "updated_at"]
    total_roots_data: int = 0

    for i in g.roots_db:
        for column in column_names:
            if column not in exceptions:
                cell_value: Optional[str] = getattr(i, column)
                if cell_value:
                    total_roots_data += 1

    line6: str = f"{total_roots_data:_} cells of Pāḷi root data"
    line6 = line6.replace("_", " ")

    g.line_6_cells_of_root_data = line6


def get_new_words(g: GlobalVars) -> None:
    """New words since the last uposatha day."""

    new_words: List[str] = [i.lemma_1 for i in g.new_words_db]
    new_words = sorted(new_words, key=pali_sort_key)
    new_words_string: str = ""
    for nw in new_words:
        # comma on all words except the last
        if nw != new_words[-1]:
            new_words_string += f"{nw}, "
        else:
            new_words_string += f"{nw} "
    new_words_string += f"[{len(new_words)}]"

    g.new_words = new_words_string


def get_github_issues_list(g: GlobalVars) -> None:
    pr.green("getting github issues")
    last_30_days: datetime = datetime.now() - timedelta(days=30)
    github: Github = Github()
    try:
        repo = github.get_repo("digitalpalidictionary/dpd-db")
        issues = repo.get_issues(state="closed", since=last_30_days, sort="number")
        pr.yes("ok")

        md: List[str] = []
        for i in issues:
            if i.milestone is not None:  # Only include issues with milestones
                md.append(rf"- [#{i.number} {i.title}]({i.html_url})")

        text: str = "\n".join(sorted(md, key=lambda x: int(x.split("#")[1].split()[0])))
        g.github_issues = text

    except Exception as e:
        pr.no("no")
        pr.red(f"GitHub not available.\n{e}")
        g.github_issues = "GitHub issues not available right now..."

    # --- other fields ---
    # i.milestone
    # i.state
    # i.created_at
    # i.updated_at
    # i.labels
    # [label.name for label in i.labels]


def make_release_notes(g: GlobalVars) -> str:
    return f"""
Digital Pāḷi Dictionary is a feature-rich Pāḷi dictionary which is available [online](https://www.dpdict.net/) and for StarDict, GoldenDict, MDict, DictTango, Kindle, Kobo, ePub and SQLite, or any application which supports these formats. It is also built into many popular [Pāḷi readers and websites](https://digitalpalidictionary.github.io/tpr.html).

It is a work in progress, made available for testing and feedback purposes.

More information about installation, setup and features can be found [on the DPD docs website](https://digitalpalidictionary.github.io/)

This work is licensed under a <a rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>

<a rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" src="https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-nc-sa.png" width="117" height="41" ></a><br />

### Github Issues Closed

{g.github_issues}

### Dictionary Data Updates

- {g.line_1_headwords}
- {g.line_2_roots}
- {g.line_3_deconstructor}
- {g.line_4_inflections}
- {g.line_5_cell_of_pali_data}
- {g.line_6_cells_of_root_data}
- Pass1 complete: VIN1-3, DN1-3, MN1-3, SN1-5, AN1-11, KN1-5, KN8-9
- Pass1 in progress: VIN4
- Pass2 complete: DN1-3, MN1
- Pass2 in progress: MN2
- numerous additions and corrections based on user feedback

"""


def make_website_changelog(g: GlobalVars) -> str:
    return f"""
## {g.date}

### Github Issues Closed
{g.github_issues}

### Dictionary Data Updates
- {g.line_1_headwords}
- {g.line_2_roots}
- {g.line_3_deconstructor}
- {g.line_4_inflections}
- {g.line_5_cell_of_pali_data}
- {g.line_6_cells_of_root_data}
- Pass1 complete: VIN1-2, DN1-3, MN1-3, SN1-5, AN1-11, KN1-5, KN8-9
- Pass1 in progress: VIN3
- Pass2 complete: DN1, MN1
- Pass2 in progress: DN2 
- numerous additions and corrections based on user feedback

### New Words
{g.new_words}
"""


def update_website_changelog(g: GlobalVars) -> None:
    pr.green("updating website changelog")

    if g.pth.docs_changelog_md_path.exists():
        changelog_md = g.pth.docs_changelog_md_path.read_text()
        find_me: str = "# Changelog"
        replace_me: str = f"# Changelog\n{g.changelog}\n"
        changelog_updated: str = changelog_md.replace(find_me, replace_me)
        g.pth.docs_changelog_md_path.write_text(changelog_updated)
        pr.yes("ok")
    else:
        pr.no("failed")
        pr.red(f"{g.pth.docs_changelog_md_path} not found")


def write_to_file(g: GlobalVars) -> None:
    with open(g.pth.release_notes_md_path, "w") as f:
        f.write(g.release_notes)

    with open(g.pth.change_log_md_path, "w") as f:
        f.write(g.changelog)


def main() -> str | None:
    pr.tic()
    pr.title("making release notes and changelog")

    if not config_test("exporter", "make_changelog", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g: GlobalVars = GlobalVars()
    get_dpd_size(g)
    get_root_size(g)
    get_deconstructor_size(g)
    get_inflection_size(g)
    get_root_data(g)
    get_new_words(g)
    get_github_issues_list(g)

    g.changelog = make_website_changelog(g)
    g.release_notes = make_release_notes(g)

    if UposathaManger.uposatha_today():
        last_id: int = g.dpd_db[-1].id
        UposathaManger.write_uposatha_count(last_id)
        update_website_changelog(g)

    write_to_file(g)

    print(g.changelog)
    pr.toc()

    return g.release_notes


if __name__ == "__main__":
    main()
