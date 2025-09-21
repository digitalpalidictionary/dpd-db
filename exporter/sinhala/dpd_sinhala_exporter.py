#!/usr/bin/env python3

"""Export Sinhala Version of DPD for GoldenDict and MDict."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.date_and_time import year_month_day_dash
from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = (
            self.db_session.query(DpdHeadword).options(joinedload(DpdHeadword.si)).all()
        )
        self.env = Environment(loader=FileSystemLoader("."))
        self.template = self.env.get_template(
            "exporter/sinhala/dpd_sinhala_template.html"
        )  # TODO add to paths


def main():
    pr.tic()
    pr.title("exporting dpd sinhala")
    pr.green("initializing data sources")
    g = GlobalVars()
    dict_data: list[DictEntry] = []
    pr.yes("ok")

    pr.green_title("making data list")
    for count, i in enumerate(g.db):
        date = year_month_day_dash()
        html = g.template.render(i=i, date=date)

        # compile synonyms
        synonyms = i.inflections_list_all  # TODO remove this once finished testing ??
        synonyms.extend(i.inflections_sinhala_list)
        synonyms.append(str(i.id))

        dict_entry = DictEntry(
            word=i.lemma_si,
            definition_html=html,
            definition_plain="",
            synonyms=synonyms,
        )

        dict_data.append(dict_entry)

        if count % 5000 == 0:  # type: ignore
            pr.counter(count, len(g.db), i.lemma_1)

    dict_info = DictInfo(
        bookname="DPD Sinhala Test",
        author="Bodhirasa",
        description="DPD Sinhala Test",
        website="https://digitalpalidictionary.github.io/",
        source_lang="pi",
        target_lang="si",
    )

    dict_var = DictVariables(
        css_paths=[Path("exporter/sinhala/dpd_sinhala.css")],
        js_paths=None,
        gd_path=g.pth.share_dir,
        md_path=g.pth.share_dir,
        dict_name="dpd-sinhala-test",
        icon_path=None,
        zip_up=True,
        delete_original=True,
    )

    export_to_goldendict_with_pyglossary(
        dict_info=dict_info,
        dict_var=dict_var,
        dict_data=dict_data,
    )

    export_to_mdict(
        dict_info=dict_info, dict_var=dict_var, dict_data=dict_data, h3_header=True
    )

    pr.toc()


if __name__ == "__main__":
    main()
