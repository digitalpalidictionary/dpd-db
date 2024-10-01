#!/usr/bin/env python3

"""Export Deconstructor To GoldenDict and MDict formats."""

import re
from mako.template import Template
from minify_html import minify
from rich import print

from exporter.goldendict.helpers import TODAY

from db.db_helpers import get_db_session
from db.models import Lookup

from tools.configger import config_test
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_title, p_yes
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.tic_toc import tic, toc, bip, bop
from tools.goldendict_exporter import DictEntry
from tools.goldendict_exporter import DictInfo, DictVariables, export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict

from exporter.goldendict.ru_components.tools.paths_ru import RuPaths
from tools.utils import squash_whitespaces


class ProgData():
    """Global variables."""
    def __init__(self) -> None:
        # config options
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict: bool = True
        elif config_test("dictionary", "make_mdict", "no"):
            self.make_mdict: bool = False
        
        # language
        if config_test("exporter", "language", "en"):
            self.lang = "en"    
        elif config_test("exporter", "language", "ru"):
            self.lang = "ru"
        else:
            raise ValueError("Invalid language parameter")
        
        # paths
        self.pth = ProjectPaths()
        self.rupth = RuPaths()

        # dict_data
        self.dict_data: list[DictEntry]


def make_deconstructor_dict_data(g: ProgData) -> None:
    """Prepare data set for GoldenDict of deconstructions and synonyms."""

    p_green("making deconstructor data list")

    db_session = get_db_session(g.pth.dpd_db_path)
    deconstructor_db = db_session \
        .query(Lookup) \
        .filter(Lookup.deconstructor!="") \
        .all()
    deconstructor_db_length: int = len(deconstructor_db)
    sandhi_contractions: dict = make_sandhi_contraction_dict(db_session)
    dict_data: list = []

    header_templ = Template(filename=str(g.pth.deconstructor_header_templ_path))
    deconstructor_header = str(header_templ.render(css="", js=""))

    if g.lang == "en":
        deconstructor_templ = Template(filename=str(g.pth.deconstructor_templ_path))
    elif g.lang == "ru":
        deconstructor_templ = Template(filename=str(g.rupth.deconstructor_templ_path))

    p_yes(len(deconstructor_db))

    for counter, i in enumerate(deconstructor_db):
        deconstructions = i.deconstructor_unpack

        # repack the deconstructions into a list of tuples
        # [0] is the deconstruction, [1] is the rules
        deconstructions_repack: list[tuple[str, str]] = []
        for d in deconstructions:
            rules = re.sub(r".+\[(.+)\]", r"\1", d)     # just whats in-between [...]
            decon = re.sub(r" \[.+", "", d)             # everything except ' [...]'
            deconstructions_repack.append((decon, rules))

        html_string: str = ""
        html_string += "<body>"
        html_string += str(deconstructor_templ.render(
            i=i,
            deconstructions=deconstructions_repack,
            today=TODAY))

        html_string += "</body></html>"
        
        html_string = squash_whitespaces(deconstructor_header) + minify(html_string)

        # make synonyms list
        synonyms = add_niggahitas([i.lookup_key], all=False)
        if g.lang != "ru":
            synonyms.extend(i.sinhala_unpack)
            synonyms.extend(i.devanagari_unpack)
            synonyms.extend(i.thai_unpack)
        if i.lookup_key in sandhi_contractions:
            contractions = sandhi_contractions[i.lookup_key]["contractions"]
            synonyms.extend(contractions)

        dict_data += [DictEntry(
            word=i.lookup_key,
            definition_html=html_string,
            definition_plain="",
            synonyms=synonyms
        )]

        if counter % 50000 == 0:
            print(
                f"{counter:>10,} / {deconstructor_db_length:<10,} {i.lookup_key[:20]:<20}{bop():>10}")
            bip()

    g.dict_data = dict_data
    p_yes(len(dict_data))


def prepare_and_export_to_gd_mdict(g: ProgData) -> None:
    
    """Prepare data to export to GoldenDict using pyglossary."""

    dict_info = DictInfo(
        bookname="DPD Deconstructor",
        author="Bodhirasa",
        description="<h3>DPD Deconstructor by Bodhirasa</h3><p>Automated compound deconstruction and sandhi-splitting of all words in <b>Chaṭṭha Saṅgāyana Tipitaka</b> and <b>Sutta Central</b> texts.</p><p>For more information please visit the <a href='https://digitalpalidictionary.github.io/deconstructor.html'>Deconstrutor page</a> on the <a href='https://digitalpalidictionary.github.io/'>DPD website</a>.</p>",
        website="https://digitalpalidictionary.github.io/deconstructor/",
        source_lang="pi",
        target_lang="pi"
    )
    dict_name = "dpd-deconstructor"
    if g.lang == "ru":
        dict_info.bookname = "DPD Деконструктор"
        dict_info.author = "Дост. Бодхираса"
        dict_info.description = "<h3>DPD Деконструктор от Дост. Бодхирасы</h3><p>Автоматизированное разложение сложных слов и разделение сандхи для всех слов в текстах Типитаки <b>Chaṭṭha Saṅgāyana</b> и на <b>Sutta Central</b>.</p><p>Дополнительную информацию можно найти на странице <a href='https://digitalpalidictionary.github.io/rus/deconstructor.html'>Деконструктора</a> на сайте <a href='https://digitalpalidictionary.github.io/rus'>DPD</a>.</p>"
        dict_info.website = "https://digitalpalidictionary.github.io/rus"

        dict_name = "ru-dpd-deconstructor"

    dict_vars = DictVariables(
        css_path = g.pth.deconstructor_css_path,
        js_paths = None,
        gd_path = g.pth.share_dir,
        md_path = g.pth.share_dir,
        dict_name = dict_name,
        icon_path = g.pth.icon_path,
        zip_up = False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_vars,
        g.dict_data)
    
    if g.make_mdict:
        export_to_mdict(
            dict_info,
            dict_vars,
            g.dict_data)


def main():
    tic()
    p_title("dpd deconstructor")   
    
    # should the program run?
    if not config_test("exporter", "make_deconstructor", "yes"):
        p_green("disabled in config.ini")
        return

    g = ProgData()
    make_deconstructor_dict_data(g)
    prepare_and_export_to_gd_mdict(g)
    toc()


if __name__ == "__main__":
    main()