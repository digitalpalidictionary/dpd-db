#!/usr/bin/env python3

"""Export Deconstructor To GoldenDict and MDict formats."""

import sys

from mako.template import Template
from minify_html import minify
from rich import print
from typing import List, Dict, Union

from exporter.goldendict.helpers import TODAY

from db.get_db_session import get_db_session
from db.models import Lookup

from tools.configger import config_test
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.tic_toc import tic, toc, bip, bop
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables, export_to_goldendict_pyglossary

from exporter.ru_components.tools.paths_ru import RuPaths
from tools.utils import squash_whitespaces


sys.path.insert(1, 'tools/writemdict')


def main():
    tic()   
    print("[bright_yellow]dpd deconstructor")
    
    # should the program run?
    if config_test("exporter", "make_deconstructor", "yes"):

        # get config options
        if config_test("dictionary", "make_mdict", "yes"):
            make_mdct: bool = True
        else:
            make_mdct: bool = False    

        if config_test("exporter", "language", "ru"):
            lang = "ru"
        elif config_test("exporter", "language", "en"):
            lang = "en"    
        else:
            raise ValueError("Invalid language parameter")
            
        pth = ProjectPaths()
        rupth = RuPaths()

        data_list = make_decon_data_list(pth, rupth, lang)

        if lang == "en":
            make_goldendict_pyglossary(pth, data_list, lang)
            if make_mdct:
                make_mdict(pth, data_list, dict_info)
        elif lang == "ru":
            make_goldendict_pyglossary(pth, data_list, lang)
            if make_mdct:
                make_mdict(rupth, data_list, dict_info)

    else:
        print("[green]disabled in config.ini")
    toc()
    

def make_decon_data_list(pth: ProjectPaths, rupth: RuPaths, lang="en"):
    """Prepare data set for GoldenDict of deconstructions and synonyms."""

    print(f"[green]{'making deconstructor data list':<40}")

    db_session = get_db_session(pth.dpd_db_path)
    decon_db = db_session.query(Lookup).filter(Lookup.deconstructor!="").all()
    decon_db_length: int = len(decon_db)
    sandhi_contractions: dict = make_sandhi_contraction_dict(db_session)
    decon_data_list: list = []

    header_templ = Template(filename=str(pth.header_deconstructor_templ_path))
    decon_header = str(header_templ.render(css="", js=""))

    if lang == "en":
        decon_templ = Template(filename=str(pth.deconstructor_templ_path))
    elif lang == "ru":
        decon_templ = Template(filename=str(rupth.deconstructor_templ_path))

    bip()
    for counter, i in enumerate(decon_db):
        deconstructions = i.deconstructor_unpack

        html_string: str = ""
        html_string += "<body>"
        html_string += str(decon_templ.render(
            i=i,
            deconstructions=deconstructions,
            today=TODAY))

        html_string += "</body></html>"
        
        html_string = squash_whitespaces(decon_header) + minify(html_string)

        # make synonyms list
        synonyms = add_niggahitas([i.lookup_key], all=False)
        if lang != "ru":
            synonyms.extend(i.sinhala_unpack)
            synonyms.extend(i.devanagari_unpack)
            synonyms.extend(i.thai_unpack)
        if i.lookup_key in sandhi_contractions:
            contractions = sandhi_contractions[i.lookup_key]["contractions"]
            synonyms.extend(contractions)

        decon_data_list += [DictEntry(
            word=i.lookup_key,
            definition_html=html_string,
            definition_plain="",
            synonyms=synonyms
        )]

        if counter % 50000 == 0:
            print(
                f"{counter:>10,} / {decon_db_length:<10,} {i.lookup_key[:20]:<20}{bop():>10}")
            bip()

    return decon_data_list


def make_goldendict_pyglossary(
    pth: ProjectPaths,
    data_list: list[DictEntry],
    lang: str
) -> None:
    
    """Prepare data to export to GoldenDict using pyglossary."""

    dict_info = DictInfo(
        bookname="DPD Deconstructor",
        author="Bodhirasa",
        description="<h3>DPD Deconstructor by Bodhirasa</h3><p>Automated compound deconstruction and sandhi-splitting of all words in <b>Chaṭṭha Saṅgāyana Tipitaka</b> and <b>Sutta Central</b> texts.</p><p>For more information please visit the <a href='https://digitalpalidictionary.github.io/deconstructor.html'>Deconstrutor page</a> on the <a href='https://digitalpalidictionary.github.io/'>DPD website</a>.</p>",
        website="https://digitalpalidictionary.github.io/deconstructor/",
        source_lang="pa",
        target_lang="en"
    )
    if lang == "ru":
        dict_info.bookname = "DPD Деконструктор"
        dict_info.author = "Дост. Бодхираса"
        dict_info.description = "<h3>DPD Деконструктор от Дост. Бодхирасы</h3><p>Автоматизированное разложение сложных слов и разделение сандхи для всех слов в текстах Типитаки <b>Chaṭṭha Saṅgāyana</b> и на <b>Sutta Central</b>.</p><p>Дополнительную информацию можно найти на странице <a href='https://digitalpalidictionary.github.io/rus/deconstructor.html'>Деконструктора</a> на сайте <a href='https://digitalpalidictionary.github.io/rus'>DPD</a>.</p>"
        dict_info.website = "https://digitalpalidictionary.github.io/rus"
        dict_info.target_lang = "ru"

    dict_vars = DictVariables(
        css_path=pth.deconstructor_css_path,
        output_path=pth.share_dir,
        dict_name="dpd-deconstructor",
        icon_path=pth.icon_path
    )

    export_to_goldendict_pyglossary(dict_info, dict_vars, data_list)


# def make_mdict(pth: Union[ProjectPaths, RuPaths], decon_data_list: List[Dict], m: Union[Metadata, RuMetadata]):
#     """Export MDict."""

#     print(f"[green]{'exporting mdct':<22}")

#     export_to_mdict(
#         decon_data_list,
#         str(pth.deconstructor_mdict_mdx_path),
#         m.title,
#         m.description)


if __name__ == "__main__":
    main()