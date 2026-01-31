#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create all the data necessary for release notes and website changelog
1. Release preamble
2. GitHub Issues Closed
3. Dictionary data
4. New Words
"""

from datetime import datetime
from typing import Dict, List, Optional

from github import Github

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, Lookup
from tools.configger import config_test
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.uposatha_day import UposathaManger


class ChangelogGenerator:
    """Generate changelog and release notes."""

    def __init__(self) -> None:
        pr.green("initializing")
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.dpd_db: List[DpdHeadword] = []
        self.roots_db: List[DpdRoot] = []
        self.deconstructor_db: List[Lookup] = []
        self.new_words_db: List[DpdHeadword] = []
        self.last_id: str = "0"
        self.github_issues: str = ""
        self.date: str = datetime.today().strftime("%Y-%m-%d")
        self.root_families: Dict[str, int] = {}
        self.line_1_headwords: str = ""
        self.line_2_roots: str = ""
        self.line_3_deconstructor: str = ""
        self.line_4_inflections: str = ""
        self.line_5_cell_of_pali_data: str = ""
        self.line_6_cells_of_root_data: str = ""
        self.new_words: str = ""
        self.release_notes: str = ""
        self.changelog: str = ""
        pr.yes("ok")

    def _load_data_from_db(self) -> None:
        """Load all necessary data from the database."""

        pr.green("loading db")
        self.dpd_db = self.db_session.query(DpdHeadword).all()
        self.roots_db = self.db_session.query(DpdRoot).all()
        self.deconstructor_db = (
            self.db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
        )
        uposatha_count = UposathaManger.read_uposatha_count()
        self.last_id = str(uposatha_count) if uposatha_count is not None else "0"
        self.new_words_db = (
            self.db_session.query(DpdHeadword)
            .filter(DpdHeadword.id > int(self.last_id))
            .all()
        )
        pr.yes(len(self.dpd_db))

    @staticmethod
    def _format_number(n: int) -> str:
        """Format a number with thousands separators."""
        return f"{n:_}".replace("_", " ")

    def _get_dpd_size(self) -> None:
        """Summary of dpd_headwords table"""
        pr.green("get dpd data")
        total_headwords = len(self.dpd_db)
        total_complete = 0
        total_partially_complete = 0
        total_incomplete = 0
        root_families: Dict[str, int] = {}
        total_data = 0

        columns = DpdHeadword.__table__.columns
        column_names = [c.name for c in columns]
        exceptions = ["id", "created_at", "updated_at"]

        for i in self.dpd_db:
            if i.meaning_1:
                if i.source_1:
                    total_complete += 1
                else:
                    total_partially_complete += 1
            else:
                total_incomplete += 1
            if i.root_key:
                subfamily = f"{i.root_key} {i.family_root}"
                root_families.setdefault(subfamily, 0)
                root_families[subfamily] += 1

            for column in column_names:
                if column not in exceptions and getattr(i, column):
                    total_data += 1

        self.line_1_headwords = (
            f"{self._format_number(total_headwords)} headwords, "
            f"{self._format_number(total_complete)} complete, "
            f"{self._format_number(total_partially_complete)} partially complete, "
            f"{self._format_number(total_incomplete)} incomplete entries"
        )
        self.line_5_cell_of_pali_data = (
            f"{self._format_number(total_data)} cells of Pāḷi word data"
        )
        self.root_families = root_families
        pr.yes("ok")

    def _get_root_size(self) -> None:
        """Summary of root families."""
        pr.green("get root data")
        total_roots = len(self.roots_db)
        total_root_families = len(self.root_families)
        total_derived_from_roots = sum(self.root_families.values())

        self.line_2_roots = (
            f"{self._format_number(total_roots)} roots, "
            f"{self._format_number(total_root_families)} root families, "
            f"{self._format_number(total_derived_from_roots)} words derived from roots"
        )
        pr.yes("ok")

    def _get_deconstructor_size(self) -> None:
        """Summary of deconstructor"""
        pr.green("get deconstructor data")
        total_deconstructions = len(self.deconstructor_db)
        self.line_3_deconstructor = (
            f"{self._format_number(total_deconstructions)} deconstructed compounds"
        )
        pr.yes("ok")

    def _get_inflection_size(self) -> None:
        """Summarize inflections."""
        pr.green("get inflection data")
        all_inflection_set: set[str] = set()
        for i in self.dpd_db:
            all_inflection_set.update(i.inflections_list)
        self.line_4_inflections = f"{self._format_number(len(all_inflection_set))} unique inflected forms recognized"
        pr.yes("ok")

    def _get_root_data(self) -> None:
        """Summarize dpd_roots table"""
        pr.green("get root data")
        columns = DpdRoot.__table__.columns
        column_names = [c.name for c in columns]
        exceptions = ["root_info", "root_matrix", "created_at", "updated_at"]
        total_roots_data = 0

        for i in self.roots_db:
            for column in column_names:
                if column not in exceptions and getattr(i, column):
                    total_roots_data += 1

        self.line_6_cells_of_root_data = (
            f"{self._format_number(total_roots_data)} cells of Pāḷi root data"
        )
        pr.yes("ok")

    def _get_new_words(self) -> None:
        """New words since the last uposatha day."""
        pr.green("get new words")
        new_words_list = sorted(
            [i.lemma_1 for i in self.new_words_db], key=pali_sort_key
        )
        if new_words_list:
            self.new_words = ", ".join(new_words_list) + f" [{len(new_words_list)}]"
        else:
            self.new_words = "[0]"
        pr.yes("ok")

    def _get_github_issues_list(self) -> None:
        pr.green("get github issues")
        github = Github()
        try:
            repo = github.get_repo("digitalpalidictionary/dpd-db")

            # Get the last release date
            latest_release = repo.get_releases()[0]
            since_date = latest_release.published_at

            issues = repo.get_issues(state="closed", since=since_date, sort="number")

            md = [
                rf"- [#{i.number} {i.title}]({i.html_url})"
                for i in issues
                if i.milestone is not None
            ]
            self.github_issues = "\n".join(
                sorted(md, key=lambda x: int(x.split("#")[1].split()[0]))
            )
            pr.yes("ok")
            pr.info(f"fetched all github issues since {since_date}")
        except Exception as e:
            pr.no("no")
            pr.red(f"GitHub not available.\n{e}")
            self.github_issues = "GitHub issues not available right now..."

    def _get_github_issues_section(self) -> str:
        return f"""
### GitHub Issues Closed
{self.github_issues}
"""

    def _get_dictionary_data_updates(self) -> str:
        return f"""
### Dictionary Data Updates
- {self.line_1_headwords}
- {self.line_2_roots}
- {self.line_3_deconstructor}
- {self.line_4_inflections}
- {self.line_5_cell_of_pali_data}
- {self.line_6_cells_of_root_data}
- Pass1 complete: VIN1-4, DN1-3, MN1-3, SN1-5, AN1-11, KN1-5, KN8-9
- Pass1 in progress: VIN5
- Pass2 complete: DN1-3, MN1-3, SN1
- Pass2 in progress: SN2
- numerous additions and corrections based on user feedback
"""

    def _make_release_notes(self) -> None:
        github_section = self._get_github_issues_section()
        data_updates_section = self._get_dictionary_data_updates()
        self.release_notes = f"""
Digital Pāḷi Dictionary is a feature-rich Pāḷi dictionary which is available [online](https://www.dpdict.net/) and for StarDict, GoldenDict, MDict, DictTango, Kindle, Kobo, ePub, SQLite, and plain text or any application which supports these formats. It is also built into many popular [Pāḷi readers and websites](https://digitalpalidictionary.github.io/tpr.html).

It is a work in progress, made available for testing and feedback purposes.

More information about installation, setup and features can be found [on the DPD docs website](https://digitalpalidictionary.github.io/)

This work is licensed under a <a rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>

<a rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" src="https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-nc-sa.png" width="117" height="41" ></a><br />

{github_section}
{data_updates_section}
"""

    def _make_website_changelog(self) -> None:
        github_section = self._get_github_issues_section()
        data_updates_section = self._get_dictionary_data_updates()
        self.changelog = f"""
## {self.date}
{github_section}
{data_updates_section}
### New Words
{self.new_words}
"""

    def _update_website_changelog(self) -> None:
        pr.green("updating website changelog")
        if self.pth.docs_changelog_md_path.exists():
            changelog_md = self.pth.docs_changelog_md_path.read_text()
            find_me = "# Changelog"
            replace_me = f"# Changelog\n{self.changelog}\n"
            changelog_updated = changelog_md.replace(find_me, replace_me)
            self.pth.docs_changelog_md_path.write_text(changelog_updated)
            pr.yes("ok")
        else:
            pr.no("failed")
            pr.red(f"{self.pth.docs_changelog_md_path} not found")

    def _write_to_file(self) -> None:
        with open(self.pth.release_notes_md_path, "w") as f:
            f.write(self.release_notes)
        with open(self.pth.change_log_md_path, "w") as f:
            f.write(self.changelog)

    def generate(self) -> Optional[str]:
        if not config_test("exporter", "make_changelog", "yes"):
            pr.green_title("disabled in config.ini")
            return None

        self._load_data_from_db()
        self._get_dpd_size()
        self._get_root_size()
        self._get_deconstructor_size()
        self._get_inflection_size()
        self._get_root_data()
        self._get_new_words()
        self._get_github_issues_list()

        self._make_website_changelog()
        self._make_release_notes()

        if UposathaManger.uposatha_today():
            if self.dpd_db:
                last_id = self.dpd_db[-1].id
                UposathaManger.write_uposatha_count(last_id)
            self._update_website_changelog()

        self._write_to_file()

        import builtins

        builtins.print(self.changelog)

        return self.release_notes


def main() -> None:
    pr.tic()
    pr.title("making release notes and changelog")
    generator = ChangelogGenerator()
    generator.generate()
    pr.toc()


if __name__ == "__main__":
    main()
