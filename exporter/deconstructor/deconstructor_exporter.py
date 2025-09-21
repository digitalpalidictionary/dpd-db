#!/usr/bin/env python3

"""Export Deconstructor To GoldenDict and MDict formats."""

from mako.template import Template
from minify_html import minify

from db.db_helpers import get_db_session
from db.models import Lookup
from exporter.goldendict.helpers import TODAY
from tools.configger import config_test
from tools.css_manager import CSSManager
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
from tools.sandhi_contraction import SandhiContractionDict, SandhiContractionManager
from tools.utils import squash_whitespaces


class GlobalVars:
    """Global variables."""

    def __init__(self) -> None:
        # config options
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict: bool = True
        elif config_test("dictionary", "make_mdict", "no"):
            self.make_mdict: bool = False

        # paths
        self.pth = ProjectPaths()

        # dict_data
        self.dict_data: list[DictEntry]


def make_deconstructor_dict_data(g: GlobalVars) -> None:
    """Prepare data set for GoldenDict of deconstructions and synonyms."""

    pr.green("making deconstructor data list")

    db_session = get_db_session(g.pth.dpd_db_path)
    deconstructor_db = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
    deconstructor_db_length: int = len(deconstructor_db)

    sandhi_finder = SandhiContractionManager()
    sandhi_contractions: SandhiContractionDict = (
        sandhi_finder.get_sandhi_contractions_simple()
    )

    dict_data: list = []

    header_templ = Template(filename=str(g.pth.deconstructor_header_templ_path))
    deconstructor_header = str(header_templ.render(css="", js=""))

    # add css variables and roots
    css_manager = CSSManager()
    deconstructor_header = css_manager.update_style(
        deconstructor_header, "deconstructor"
    )

    deconstructor_templ = Template(filename=str(g.pth.deconstructor_templ_path))

    pr.yes(len(deconstructor_db))

    for counter, i in enumerate(deconstructor_db):
        deconstructions = i.deconstructor_unpack

        html_string: str = ""
        html_string += "<body>"
        html_string += str(
            deconstructor_templ.render(
                i=i, deconstructions=deconstructions, today=TODAY
            )
        )

        html_string += "</body></html>"

        html_string = squash_whitespaces(deconstructor_header) + minify(html_string)

        # make synonyms list
        synonyms = add_niggahitas([i.lookup_key], all=False)
        synonyms.extend(i.sinhala_unpack)
        synonyms.extend(i.devanagari_unpack)
        synonyms.extend(i.thai_unpack)
        if i.lookup_key in sandhi_contractions:
            contractions = sandhi_contractions.get(i.lookup_key, [])
            synonyms.extend(contractions)

        dict_data += [
            DictEntry(
                word=i.lookup_key,
                definition_html=html_string,
                definition_plain="",
                synonyms=synonyms,
            )
        ]

        if counter % 50000 == 0:
            pr.counter(counter, deconstructor_db_length, i.lookup_key)

    g.dict_data = dict_data
    pr.yes(len(dict_data))


def prepare_and_export_to_gd_mdict(g: GlobalVars) -> None:
    """Prepare data to export to GoldenDict using pyglossary."""

    dict_info = DictInfo(
        bookname="DPD Deconstructor",
        author="Bodhirasa",
        description="<h3>DPD Deconstructor by Bodhirasa</h3><p>Automated compound deconstruction and sandhi-splitting of all words in <b>Chaṭṭha Saṅgāyana Tipitaka</b> and <b>Sutta Central</b> texts.</p><p>For more information please visit the <a href='https://digitalpalidictionary.github.io/features/deconstructor/'>Deconstrutor page</a> on the <a href='https://digitalpalidictionary.github.io'>DPD website</a>.</p>",
        website="https://digitalpalidictionary.github.io/features/deconstructor/",
        source_lang="pi",
        target_lang="pi",
    )
    dict_name = "dpd-deconstructor"

    dict_vars = DictVariables(
        css_paths=[g.pth.dpd_css_and_fonts_path],
        js_paths=None,
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


def main():
    pr.tic()
    pr.title("dpd deconstructor")

    # should the program run?
    if not config_test("exporter", "make_deconstructor", "yes"):
        pr.green("disabled in config.ini")
        return

    g = GlobalVars()
    make_deconstructor_dict_data(g)
    prepare_and_export_to_gd_mdict(g)
    pr.toc()


if __name__ == "__main__":
    main()
