"""Compile HTML data for ru Help, Abbreviations, Thanks & Bibliography."""

import csv
# import html2text

from css_html_js_minify import css_minify
from mako.template import Template
from minify_html import minify
from rich import print
from typing import List, Dict, Tuple

from sqlalchemy.orm import Session
from dps.tools.paths_dps import DPSPaths

from export_dpd import render_header_templ
from export_help import Abbreviation, Help
from export_help import add_bibliographhy, add_thanks

from tools.paths import ProjectPaths
from tools.tic_toc import bip, bop
from tools.tsv_read_write import read_tsv_dict
# from tools.tsv_read_write import read_tsv_dot_dict
from tools.utils import RenderResult, RenderedSizes, default_rendered_sizes
# from tools.configger import config_test


# class Abbreviation:
#     """defining the abbreviations.tsv columns"""

#     def __init__(self, abbrev, meaning, pali, example, information, ru_abbrev, ru_meaning):
#         self.abbrev = abbrev
#         self.meaning = meaning
#         self.pali = pali
#         self.example = example
#         self.information = information
#         self.ru_abbrev = ru_abbrev
#         self.ru_meaning = ru_meaning

#     def __repr__(self) -> str:
#         return f"Abbreviation: {self.abbrev} {self.meaning} {self.pali} ..."


# class Help:
#     """defining the help.tsv columns"""

#     def __init__(self, help, meaning, ru_help, ru_meaning):
#         self.help = help
#         self.meaning = meaning
#         self.ru_help = ru_help
#         self.ru_meaning = ru_meaning

#     def __repr__(self) -> str:
#         return f"Help: {self.help} {self.meaning}  ..."


def generate_help_html(__db_session__: Session,
                       pth: ProjectPaths,
                       dpspth: DPSPaths) -> Tuple[List[RenderResult], RenderedSizes]:
    """generating html of all help files used in the dictionary"""
    print("[green]generating help html")

    size_dict = default_rendered_sizes()

    # 1. abbreviations
    # 2. contextual help
    # 3. thank yous
    # 4. bibliography


    with open(pth.help_css_path) as f:
        css = f.read()
    css = css_minify(css)

    header_templ = Template(filename=str(pth.header_templ_path))
    header = render_header_templ(
        pth, css=css, js="", header_templ=header_templ)

    help_data_list: List[RenderResult] = []

    abbrev = add_abbrev_html(pth, dpspth, header)
    help_data_list.extend(abbrev)
    size_dict["help"] += len(str(abbrev))

    help_html = add_help_html(pth, dpspth, header)
    help_data_list.extend(help_html)
    size_dict["help"] += len(str(help_html))

    bibliography = add_bibliographhy(pth, header)
    help_data_list.extend(bibliography)
    size_dict["help"] += len(str(bibliography))

    thanks = add_thanks(pth, header)
    help_data_list.extend(thanks)
    size_dict["help"] += len(str(thanks))

    return help_data_list, size_dict


def add_abbrev_html(pth: ProjectPaths, dpspth: DPSPaths,
                    header: str) -> List[RenderResult]:
    bip()
    print("adding abbreviations", end=" ")

    help_data_list = []

    file_path = pth.abbreviations_tsv_path
    rows = read_tsv_dict(file_path)

    rows2 = []
    with open(pth.abbreviations_tsv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows2.append(row)

    assert rows == rows2

    def _csv_row_to_abbreviations(x: Dict[str, str]) -> Abbreviation:
        return Abbreviation(
            abbrev=x["abbrev"],
            meaning=x["meaning"],
            pali=x["pāli"],
            example=x["example"],
            information=x["explanation"],
            ru_abbrev=x["ru_abbrev"],
            ru_meaning=x["ru_meaning"])

    items = list(map(_csv_row_to_abbreviations, rows))

    for i in items:
        html = header
        html += "<body>"
        html += render_abbrev_templ(dpspth, i)
        html += "</body></html>"

        html = minify(html)

        res = RenderResult(
            word = i.ru_abbrev,
            definition_html = html,
            definition_plain = "",
            synonyms = [],
        )

        help_data_list.append(res)

    print(f"{bop():>34}")
    return help_data_list


def add_help_html(pth: ProjectPaths, dpspth: DPSPaths,
                    header: str) -> List[RenderResult]:
    bip()
    print("adding help", end=" ")

    help_data_list = []

    file_path = pth.help_tsv_path
    rows = read_tsv_dict(file_path)

    rows2 = []
    with open(pth.help_tsv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows2.append(row)

    assert rows == rows2

    def _csv_row_to_help(x: Dict[str, str]) -> Help:
        return Help(
            help=x["help"],
            meaning=x["meaning"],
            ru_help=x["ru_help"],
            ru_meaning=x["ru_meaning"]
        )

    items = list(map(_csv_row_to_help, rows))

    for i in items:
        html = header
        html += "<body>"
        html += render_help_templ(dpspth, i)
        html += "</body></html>"

        html = minify(html)

        res = RenderResult(
            word = i.ru_help,
            definition_html = html,
            definition_plain = "",
            synonyms = [],
        )

        help_data_list.append(res)

    print(f"{bop():>43}")
    return help_data_list







def render_abbrev_templ(dpspth: DPSPaths, i: Abbreviation) -> str:
    """render html of abbreviations"""

    abbrev_templ = Template(filename=str(dpspth.abbrev_templ_path))

    return str(abbrev_templ.render(i=i))


def render_help_templ(dpspth: DPSPaths, i: Help) -> str:
    """render html of help"""

    help_templ = Template(filename=str(dpspth.help_templ_path))

    return str(help_templ.render(i=i))
