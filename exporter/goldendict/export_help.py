# -*- coding: utf-8 -*-
"""Compile HTML data for Help, Abbreviations, Thanks & Bibliography."""

import csv
from typing import Dict, List, Tuple

from minify_html import minify
from sqlalchemy.orm import Session

from tools.goldendict_exporter import DictEntry
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dict, read_tsv_dot_dict
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes import AbbreviationsData, HelpData


class Abbreviation:
    """defining the abbreviations.tsv columns"""

    def __init__(
        self,
        abbrev,
        meaning,
        pali,
        example,
        information,
    ):
        self.abbrev = abbrev
        self.meaning = meaning
        self.pali = pali
        self.example = example
        self.information = information


class Help:
    """defining the help.tsv columns"""

    def __init__(
        self,
        help,
        meaning,
    ):
        self.help = help
        self.meaning = meaning


def generate_help_html(
    __db_session__: Session,
    pth: ProjectPaths,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generating html of all help files used in the dictionary"""
    pr.green("generating help html")

    size_dict = default_rendered_sizes()

    jinja_env = get_jinja2_env("exporter/goldendict/templates")

    help_data_list: List[DictEntry] = []

    abbrev = add_abbrev_html(pth, jinja_env)
    help_data_list.extend(abbrev)
    size_dict["help"] += len(str(abbrev))

    help_html = add_help_html(pth, jinja_env)
    help_data_list.extend(help_html)
    size_dict["help"] += len(str(help_html))

    # Header for bibliography and thanks
    dummy_data = AbbreviationsData(None, jinja_env)
    header = dummy_data.header

    bibliography = add_bibliography(pth, header)
    help_data_list.extend(bibliography)
    size_dict["help"] += len(str(bibliography))

    thanks = add_thanks(pth, header)
    help_data_list.extend(thanks)
    size_dict["help"] += len(str(thanks))

    pr.yes(len(help_data_list))
    return help_data_list, size_dict


def add_abbrev_html(
    pth: ProjectPaths,
    jinja_env,
) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.abbreviations_tsv_path
    rows = read_tsv_dict(file_path)

    def _csv_row_to_abbreviations(x: Dict[str, str]) -> Abbreviation:
        return Abbreviation(
            abbrev=x["abbrev"],
            meaning=x["meaning"],
            pali=x["pāli"],
            example=x["example"],
            information=x["explanation"],
        )

    items = list(map(_csv_row_to_abbreviations, rows))
    template = jinja_env.get_template("help_abbrev.jinja")

    for i in items:
        data = AbbreviationsData(i, jinja_env)
        html_rendered = template.render(d=data)

        # Re-calculate parts for parity
        header = data.header
        body_start = html_rendered.find("<body>")
        body = html_rendered[body_start:]
        
        final_html = squash_whitespaces(header) + minify(body)

        help_data_list.append(DictEntry(
            word=i.abbrev,
            definition_html=final_html,
            definition_plain="",
            synonyms=[],
        ))

    return help_data_list


def add_help_html(
    pth: ProjectPaths,
    jinja_env,
) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.help_tsv_path
    rows = read_tsv_dict(file_path)

    def _csv_row_to_help(x: Dict[str, str]) -> Help:
        return Help(
            help=x["help"],
            meaning=x["meaning"],
        )

    items = list(map(_csv_row_to_help, rows))
    template = jinja_env.get_template("help_help.jinja")

    for i in items:
        data = HelpData(i, jinja_env)
        html_rendered = template.render(d=data)

        # Re-calculate parts for parity
        header = data.header
        body_start = html_rendered.find("<body>")
        body = html_rendered[body_start:]
        
        final_html = squash_whitespaces(header) + minify(body)

        help_data_list.append(DictEntry(
            word=i.help,
            definition_html=final_html,
            definition_plain="",
            synonyms=[],
        ))

    return help_data_list


def add_bibliography(pth: ProjectPaths, header: str) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.bibliography_tsv_path
    bibliography_dict = read_tsv_dot_dict(file_path)

    html = ""
    html += "<body>"
    html += "<div class='tertiary'>"
    html += "<h2>Bibliography</h2>"

    for x in range(len(bibliography_dict)):
        i = bibliography_dict[x]
        if x + 1 > len(bibliography_dict) - 1:
            break
        else:
            n = bibliography_dict[x + 1]

        if i.category:
            html += f"<h3 class='dpd'>{i.category}</h3>"
            html += "<ul>"
        if i.surname:
            html += f"<li><b>{i.surname}</b>"
        if i.firstname:
            html += f", {i.firstname}"
        if i.year:
            html += f", {i.year}"
        if i.title:
            html += f". <i>{i.title}</i>"
        if i.city and i.publisher:
            html += f", {i.city}: {i.publisher}"
        if not i.city and i.publisher:
            html += f", {i.publisher}"
        if i.site:
            html += (
                f", accessed through <a href='{i.site}'  target='_blank'>{i.site}</a>"
            )
        if i.surname:
            html += "</li>"

        if n.category:
            html += "</ul>"

    html += "</div></body></html>"
    html = squash_whitespaces(header) + minify(html)

    help_data_list.append(DictEntry(
        word="bibliography",
        definition_html=html,
        definition_plain="",
        synonyms=["dpd bibliography", "bibliography", "bib"],
    ))

    return help_data_list


def add_thanks(pth: ProjectPaths, header: str) -> List[DictEntry]:
    help_data_list = []

    file_path = pth.thanks_tsv_path
    thanks = read_tsv_dot_dict(file_path)

    html = ""
    html += "<body>"
    html += "<div class='tertiary'>"

    for x in range(len(thanks)):
        i = thanks[x]
        if x + 1 > len(thanks) - 1:
            break
        else:
            n = thanks[x + 1]

        if i.category:
            html += f"<h2>{i.category}</h2>"
            html += f"<p>{i.what}</p>"
            html += "<ul>"
        if i.who:
            html += f"<li><b>{i.who}</b>"
        if i.where:
            html += f" {i.where}"
        if i.what and not i.category:
            html += f" {i.what}"
        if i.who:
            html += "</li>"

        if n.category:
            html += "</ul>"

    html += "</div></body></html>"
    html = squash_whitespaces(header) + minify(html)

    help_data_list.append(DictEntry(
        word="thanks",
        definition_html=html,
        definition_plain="",
        synonyms=["dpd thanks", "thankyou", "thanks", "anumodana"],
    ))

    return help_data_list
