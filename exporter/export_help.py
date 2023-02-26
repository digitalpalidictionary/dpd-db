import csv
import markdown

from pathlib import Path
from rich import print
from typing import List, Dict

from html_components import render_header_tmpl
from html_components import render_abbrev_templ
from html_components import render_help_templ

from tools.timeis import bip, bop


class Abbreviation:
    """defining the abbreviations.tsv columns"""

    def __init__(self, abbrev, meaning, pali, example, information):
        self.abbrev = abbrev
        self.meaning = meaning
        self.pali = pali
        self.example = example
        self.information = information

    def __repr__(self) -> str:
        return f"Abbreviation: {self.abbrev} {self.meaning} {self.pali} ..."


class Help:
    """defining the help.tsv columns"""

    def __init__(self, help, meaning):
        self.help = help
        self.meaning = meaning

    def __repr__(self) -> str:
        return f"Help: {self.help} {self.meaning}  ..."


def generate_help_html(DB_SESSION, PTH: Path) -> list:
    """genrating html of all help files used in the dictionary"""
    print("[green]generating help html")

    # 1. abbreviations
    # 2. contextual help
    # 3. thanks you
    # 4. bibliography

    with open(PTH.help_css_path) as f:
        css = f.read()
        js = ""

    header = render_header_tmpl(css, js)
    help_data_list: List[dict] = []

    help_data_list = add_abbrev_html(PTH, header, help_data_list)
    help_data_list = add_help_html(PTH, header, help_data_list)
    help_data_list = add_bibliographhy(PTH, header, help_data_list)
    help_data_list = add_thanks(PTH, header, help_data_list)

    return help_data_list


def add_abbrev_html(PTH: Path, header: str, help_data_list: list) -> list:
    bip()
    print("adding abbreviations", end=" ")

    rows = []
    with open(PTH.abbrev_tsv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)

    def _csv_row_to_abbreviations(x: Dict[str, str]) -> Abbreviation:
        return Abbreviation(
            abbrev=x["abbrev"],
            meaning=x["meaning"],
            pali=x["pāli"],
            example=x["example"],
            information=x["explanation"])

    items = list(map(_csv_row_to_abbreviations, rows))

    for i in items:
        html = header
        html += "<body>"
        html += render_abbrev_templ(i)
        html += "</body></html>"

        help_data_list += [{
            "word": i.abbrev,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": ""
        }]

    print(f"{bop():>34}")
    return help_data_list


def add_help_html(PTH: Path, header: str, help_data_list: list) -> list:
    bip()
    print("adding help", end=" ")

    rows = []
    with open(PTH.help_tsv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)

    def _csv_row_to_help(x: Dict[str, str]) -> Help:
        return Help(
            help=x["help"],
            meaning=x["meaning"]
        )

    items = list(map(_csv_row_to_help, rows))

    for i in items:
        html = header
        html += "<body>"
        html += render_help_templ(i)
        html += "</body></html>"

        help_data_list += [{
            "word": i.help,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": ""
        }]

    with open(f"xxx delete/exporter_help/{i.help}.html", "w") as f:
        f.write(html)

    print(f"{bop():>43}")
    return help_data_list


def add_bibliographhy(PTH: Path, header: str, help_data_list: list) -> list:

    print(f"adding bibliography", end=" ")

    with open(PTH.bibliography_path) as f:
        md = f.read()

    html = header
    html += "<body>"
    html += "<div class='help'>"
    html += markdown.markdown(md)
    html += "</div></body></html>"

    synonyms = ["dpd bibliography", "bibliography", "bib"]

    help_data_list += [{
        "word": "bibliography",
        "definition_html": html,
        "definition_plain": "",
        "synonyms": synonyms
    }]

    with open(f"xxx delete/exporter_help/bibliography.html", "w") as f:
        f.write(html)

    print(f"{bop():>35}")
    return help_data_list


def add_thanks(PTH: Path, header: str, help_data_list: list) -> list:

    print(f"adding thanks", end=" ")

    with open(PTH.thanks_path) as f:
        md = f.read()

    html = header
    html += "<body>"
    html += "<div class='help'>"
    html += markdown.markdown(md)
    html += "</div></body></html>"

    synonyms = ["dpd thanks", "thankyou", "thanks", "anumodana"]

    help_data_list += [{
        "word": "thanks",
        "definition_html": html,
        "definition_plain": "",
        "synonyms": synonyms
    }]

    with open(f"xxx delete/exporter_help/thanks.html", "w") as f:
        f.write(html)

    print(f"{bop():>41}")
    return help_data_list
