"""Compile HTML data for Help, Abbreviations, Thanks & Bibliography."""

import csv
import html2text

from mako.template import Template
from minify_html import minify
from typing import List, Dict, Tuple

from sqlalchemy.orm import Session

from tools.paths import ProjectPaths
from exporter.goldendict.ru_components.tools.paths_ru import RuPaths
from tools.printer import p_green, p_yes
from tools.tsv_read_write import read_tsv_dict
from tools.tsv_read_write import read_tsv_dot_dict
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces
from tools.goldendict_exporter import DictEntry

class Abbreviation:
    """defining the abbreviations.tsv columns"""

    def __init__(self, abbrev, meaning, pali, example, information, ru_abbrev, ru_meaning):
        self.abbrev = abbrev
        self.meaning = meaning
        self.pali = pali
        self.example = example
        self.information = information
        self.ru_abbrev = ru_abbrev
        self.ru_meaning = ru_meaning

    def __repr__(self) -> str:
        return f"Abbreviation: {self.abbrev} {self.meaning} {self.pali} ..."


class Help:
    """defining the help.tsv columns"""

    def __init__(self, help, meaning, ru_help, ru_meaning):
        self.help = help
        self.meaning = meaning
        self.ru_help = ru_help
        self.ru_meaning = ru_meaning

    def __repr__(self) -> str:
        return f"Help: {self.help} {self.meaning}  ..."


def generate_help_html(
    __db_session__: Session,
    pth: ProjectPaths,
    rupth: RuPaths,
    lang="en",
    show_ru_data=False
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generating html of all help files used in the dictionary"""
    p_green("generating help html")

    size_dict = default_rendered_sizes()

    # 1. abbreviations
    # 2. contextual help
    # 3. thank yous
    # 4. bibliography

    if lang == "en":
        header_templ = Template(filename=str(pth.dpd_header_plain_templ_path))
    elif lang == "ru":
        header_templ = Template(filename=str(rupth.dpd_header_plain_templ_path))

    header = str(header_templ.render())

    help_data_list: List[DictEntry] = []

    abbrev = add_abbrev_html(pth, header, rupth, lang, show_ru_data)
    help_data_list.extend(abbrev)
    size_dict["help"] += len(str(abbrev))

    help_html = add_help_html(pth, header, rupth, lang, show_ru_data)
    help_data_list.extend(help_html)
    size_dict["help"] += len(str(help_html))

    bibliography = add_bibliography(pth, header)
    help_data_list.extend(bibliography)
    size_dict["help"] += len(str(bibliography))

    thanks = add_thanks(pth, header)
    help_data_list.extend(thanks)
    size_dict["help"] += len(str(thanks))

    p_yes(len(help_data_list))
    return help_data_list, size_dict


def add_abbrev_html(
    pth: ProjectPaths,
    header: str,
    rupth: RuPaths,
    lang="en",
    show_ru_data=False
) -> List[DictEntry]:

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
        html = ""
        html += "<body>"
        html += render_abbrev_templ(pth, i, rupth, lang, show_ru_data)
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        if lang == "en":
            word = i.abbrev
        elif lang == "ru":
            if i.ru_abbrev:
                word = i.ru_abbrev
            else:
                word = i.abbrev

        res = DictEntry(
            word = word,
            definition_html = html,
            definition_plain = "",
            synonyms = [],
        )

        help_data_list.append(res)

    return help_data_list


def add_help_html(
    pth: ProjectPaths,
    header: str,
    rupth: RuPaths,
    lang="en",
    show_ru_data=False
) -> List[DictEntry]:

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
        html = ""
        html += "<body>"
        html += render_help_templ(pth, i, rupth, lang, show_ru_data)
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        if lang == "en":
            word = i.help
        elif lang == "ru":
            word = i.ru_help

        res = DictEntry(
            word = word,
            definition_html = html,
            definition_plain = "",
            synonyms = [],
        )

        help_data_list.append(res)

    return help_data_list


def add_bibliography(
    pth: ProjectPaths,
    header: str
) -> List[DictEntry]:

    help_data_list = []

    file_path = pth.bibliography_tsv_path
    bibliography_dict = read_tsv_dot_dict(file_path)

    html = ""
    html += "<body>"
    html += "<div class='help'>"
    html += "<h2>Bibliography</h1>"

    # i = current item, n = next item
    for x in range(len(bibliography_dict)):
        i = bibliography_dict[x]
        if x+1 > len(bibliography_dict)-1:
            break
        else:
            n = bibliography_dict[x+1]

        if i.category:
            html += f"<h3>{i.category}</h3>"
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
            html += f", accessed through <a href='{i.site}'  target='_blank'>{i.site}</a>"
        if i.surname:
            html += "</li>"

        if n.category:
            html += "</ul>"

    html += "</div></body></html>"

    html = squash_whitespaces(header) + minify(html)

    synonyms = ["dpd bibliography", "bibliography", "bib"]

    res = DictEntry(
        word = "bibliography",
        definition_html = html,
        definition_plain = "",
        synonyms = synonyms,
    )

    help_data_list.append(res)

    # save markdown for website

    if pth.bibliography_md_path.exists():
        md = html2text.html2text(html)
        with open(pth.bibliography_md_path, "w") as file:
            file.write(md)

    return help_data_list


def add_thanks(
    pth: ProjectPaths,
    header: str
) -> List[DictEntry]:

    help_data_list = []

    file_path = pth.thanks_tsv_path
    thanks = read_tsv_dot_dict(file_path)

    html = ""
    html += "<body>"
    html += "<div class='help'>"

    # i = current item, n = next item
    for x in range(len(thanks)):
        i = thanks[x]
        if x+1 > len(thanks)-1:
            break
        else:
            n = thanks[x+1]

        if i.category:
            html += f"<h2>{i.category}</h2>"
            html += f"<p>{i.what}</p>"
            html += "<ul>"
        if i. who:
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

    synonyms = ["dpd thanks", "thankyou", "thanks", "anumodana"]

    res = DictEntry(
        word = "thanks",
        definition_html = html,
        definition_plain = "",
        synonyms = synonyms,
    )

    help_data_list.append(res)

    # save markdown for website
    if pth.thanks_md_path.exists():
        md = html2text.html2text(html)
        with open(pth.thanks_md_path, "w") as file:
            file.write(md)

    return help_data_list


def render_abbrev_templ( 
            pth: ProjectPaths, 
            i: Abbreviation,
            rupth: RuPaths,
            lang="en",
            show_ru_data=False
            ) -> str:
    """render html of abbreviations"""

    if lang == "en":
        abbrev_templ = Template(filename=str(pth.abbrev_templ_path))
    elif lang == "ru":
        abbrev_templ = Template(filename=str(rupth.abbrev_templ_path))

    return str(abbrev_templ.render(i=i, show_ru_data=show_ru_data))


def render_help_templ( 
            pth: ProjectPaths, 
            i: Help,
            rupth: RuPaths,
            lang="en",
            show_ru_data=False
            ) -> str:
    """render html of help"""

    if lang == "en":
        help_templ = Template(filename=str(pth.help_templ_path))
    elif lang == "ru":
        help_templ = Template(filename=str(rupth.help_templ_path))

    return str(help_templ.render(i=i, show_ru_data=show_ru_data))
