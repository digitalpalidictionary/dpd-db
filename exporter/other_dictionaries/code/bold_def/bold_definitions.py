# -*- coding: utf-8 -*-
from pathlib import Path

from jinja2 import Template

from db.db_helpers import get_db_session
from db.models import BoldDefinition
from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class BoldDefinitions:
    """Export CST Bold Definitions to Goldendict and MDict"""

    def __init__(self):
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.template = self._load_template()

    def _load_template(self) -> Template:
        template_path = Path(
            "exporter/other_dictionaries/code/bold_def/bold_definitions.html"
        )
        with open(template_path, encoding="utf-8") as f:
            return Template(f.read())

    def run(self):
        pr.tic()
        pr.title("exporting bold definitions")
        pr.green("setting up db and templates")

        dict_info = self._get_dict_info()
        dict_vars = self._get_dict_vars()

        bd_db = self.db_session.query(BoldDefinition).all()
        pr.yes(len(bd_db))

        dict_data = self.make_dict_data(bd_db)

        export_to_goldendict_with_pyglossary(dict_info, dict_vars, dict_data)
        export_to_mdict(dict_info, dict_vars, dict_data)

        pr.toc()

    def _get_dict_info(self) -> DictInfo:
        return DictInfo(
            bookname="CST Bold Definitions",
            author="Bodhirasa Bhikkhu",
            description="Extracted from Chaṭṭha Saṅgāyana Tipiṭaka",
            website="dpdict.net/?tab=bd&q1=&q2=&option=regex",
            source_lang="pi",
            target_lang="pi",
        )

    def _get_dict_vars(self) -> DictVariables:
        return DictVariables(
            css_paths=None,
            js_paths=None,
            gd_path=Path("exporter/other_dictionaries/goldendict/"),
            md_path=Path("exporter/other_dictionaries/mdict/"),
            dict_name="bold_definitions",
            icon_path=None,
            zip_up=True,
            delete_original=True,
        )

    def make_dict_data(self, bd_db: list[BoldDefinition]) -> list[DictEntry]:
        pr.green_title("making dict data")
        dict_data = []
        total = len(bd_db)
        bd_entry: BoldDefinition

        for counter, bd_entry in enumerate(bd_db):
            dict_entry = self.make_dict_entry(bd_entry)
            dict_data.append(dict_entry)
            if counter % 50000 == 0:
                pr.counter(counter, total, bd_entry.bold)
        return dict_data

    def make_dict_entry(self, bd_entry: BoldDefinition) -> DictEntry:
        word = f"{bd_entry.bold}"
        definition_html = self.template.render(bd=bd_entry)
        return DictEntry(
            word=word,
            definition_html=definition_html,
            definition_plain="",
            synonyms=[],
        )


if __name__ == "__main__":
    bd = BoldDefinitions()
    bd.run()
