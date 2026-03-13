#!/usr/bin/env python3

"""Compile HTML table of all grammatical possibilities of every inflected word-form."""

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.configger import config_test
from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from exporter.jinja2_env import get_jinja2_env
from exporter.grammar_dict.data_classes import GrammarData


class GlobalVars:
    def __init__(self) -> None:
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict = True
        else:
            self.make_mdict = False

        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        # the grammar dictionaries
        self.html_dict: dict[str, str] = {}

        # goldendict and mdict data_list
        self.dict_data: list[DictEntry] = []

    def close_db(self):
        self.db_session.close()

    def commit_db(self):
        self.db_session.commit()


def main():
    pr.tic()
    pr.yellow_title("exporting grammar dictionary")

    if not config_test("exporter", "make_grammar", "yes"):
        pr.green_tmr("disabled in config.ini")
        pr.toc()
        return

    g = GlobalVars()

    generate_html_from_lookup(g)

    g.close_db()

    make_data_lists(g)
    prepare_gd_mdict_and_export(g)

    pr.toc()


def generate_html_from_lookup(g: GlobalVars):
    """Generate HTML grammar tables from Lookup table data."""
    pr.green_tmr("querying database")

    lookup_results = (
        g.db_session.query(Lookup)
        .filter(Lookup.grammar.is_not(None), Lookup.grammar != "")
        .all()
    )

    pr.yes(f"{len(lookup_results)}")

    pr.green_tmr("compiling html")

    jinja_env = get_jinja2_env("exporter/grammar_dict")
    template = jinja_env.get_template("grammar.jinja")

    html_dict = {}
    grammar_cache: dict[str, str] = {}

    for lookup_entry in lookup_results:
        inflected_word = lookup_entry.lookup_key
        grammar_data = lookup_entry.grammar

        if grammar_data in grammar_cache:
            entry_html = grammar_cache[grammar_data]
        else:
            # Use ViewModel
            data = GrammarData(lookup_entry, g.pth, jinja_env)
            entry_html = template.render(data=data)
            grammar_cache[grammar_data] = entry_html

        html_dict[inflected_word] = entry_html

    g.html_dict = html_dict
    pr.yes(len(html_dict))


def make_data_lists(g: GlobalVars):
    """Make the data_lists to be consumed by GoldenDict and MDict"""
    pr.green_tmr("making data lists")

    dict_data: list[DictEntry] = []
    for word, html in g.html_dict.items():
        synonyms = add_niggahitas([word])

        dict_data += [
            DictEntry(
                word=word, definition_html=html, definition_plain="", synonyms=synonyms
            )
        ]

    g.dict_data = dict_data
    pr.yes("ok")


def prepare_gd_mdict_and_export(g: GlobalVars):
    """Prepare the metadata and export to goldendict & mdict."""

    dict_info = DictInfo(
        bookname="DPD Grammar",
        author="Bodhirasa",
        description="<h3>DPD Grammar</h3><p>A table of all the grammatical possibilities that a particular inflected word may have. For more information please visit the <a href='https://digitalpalidictionary.github.io/features/grammardict/' target='_blank'>DPD website</a></p>",
        website="https://digitalpalidictionary.github.io/features/grammardict/",
        source_lang="pi",
        target_lang="en",
    )
    dict_name = "dpd-grammar"

    dict_vars = DictVariables(
        css_paths=[g.pth.dpd_css_and_fonts_path],
        js_paths=[g.pth.sorter_js_path],
        gd_path=g.pth.share_dir,
        md_path=g.pth.share_dir,
        dict_name=dict_name,
        icon_path=g.pth.dpd_logo_svg,
        font_path=g.pth.fonts_dir,
        zip_up=False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(dict_info, dict_vars, g.dict_data)

    if g.make_mdict:
        export_to_mdict(dict_info, dict_vars, g.dict_data)


if __name__ == "__main__":
    main()
