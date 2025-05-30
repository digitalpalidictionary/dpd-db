"""Compile HTML data for English to Pāḷi dictionary."""

import re

from mako.template import Template
from minify_html import minify
from sqlalchemy.orm import Session
from typing import List, Tuple

from db.db_helpers import get_db_session

from db.models import DpdHeadword, DpdRoot
from tools.css_manager import CSSManager
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces
from tools.goldendict_exporter import DictEntry


def generate_epd_html(
    db_session: Session,
    pth: ProjectPaths,
    make_link=False,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generate html for english to pali dictionary"""

    size_dict = default_rendered_sizes()

    pr.green("generating epd html")

    dpd_db: list[DpdHeadword] = db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    roots_db: list[DpdRoot] = db_session.query(DpdRoot).all()

    epd: dict = {}
    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]

    header_templ = Template(filename=str(pth.dpd_header_plain_templ_path))

    header = str(header_templ.render())

    # Add Variables and fonts
    css_manager = CSSManager()
    header = css_manager.update_style(header, "primary")

    for counter, i in enumerate(dpd_db):
        # generate eng-pali
        meanings_list = []
        i.meaning_1 = re.sub(r"\?\?", "", i.meaning_1)

        if i.meaning_1 and i.pos not in pos_exclude_list:
            # remove all space brackets
            meanings_clean = re.sub(r" \(.+?\)", "", i.meaning_1)
            # remove all brackets space
            meanings_clean = re.sub(r"\(.+?\) ", "", meanings_clean)
            # remove space at start and fin
            meanings_clean = re.sub(r"(^ | $)", "", meanings_clean)
            # remove double spaces
            meanings_clean = re.sub(r"  ", " ", meanings_clean)
            # remove space around ;
            meanings_clean = re.sub(r" ;|; ", ";", meanings_clean)
            # remove i.e.
            meanings_clean = re.sub(r"i\.e\. ", "", meanings_clean)
            # remove !
            meanings_clean = re.sub(r"!", "", meanings_clean)
            # remove ?
            meanings_clean = re.sub(r"\\?", "", meanings_clean)
            meanings_list = meanings_clean.split(";")

            for meaning in meanings_list:
                if meaning in epd.keys() and not i.plus_case:
                    epd_string = f"{epd[meaning]}<br><b class='epd'>{i.lemma_clean}</b> {i.pos}. {i.meaning_1}"
                    epd[meaning] = epd_string

                if meaning in epd.keys() and i.plus_case:
                    epd_string = f"{epd[meaning]}<br><b class='epd'>{i.lemma_clean}</b> {i.pos}. {i.meaning_1} ({i.plus_case})"
                    epd[meaning] = epd_string

                if meaning not in epd.keys() and not i.plus_case:
                    epd_string = (
                        f"<b class='epd'>{i.lemma_clean}</b> {i.pos}. {i.meaning_1}"
                    )
                    epd.update({meaning: epd_string})

                if meaning not in epd.keys() and i.plus_case:
                    epd_string = f"<b class='epd'>{i.lemma_clean}</b> {i.pos}. {i.meaning_1} ({i.plus_case})"
                    epd.update({meaning: epd_string})

        # Generate links for suttas
        if i.meaning_2 and (
            i.family_set.startswith("suttas of")
            or i.family_set == "bhikkhupātimokkha rules"
            or i.family_set == "chapters of the Saṃyutta Nikāya"
        ):
            combined_numbers = extract_sutta_numbers(i.meaning_2)
            update_epd(epd, combined_numbers, i, make_link)

    for counter, i in enumerate(roots_db):
        root_meanings_list: list = i.root_meaning.split(", ")

        for root_meaning in root_meanings_list:
            if root_meaning in epd.keys():
                epd_string = f"{epd[root_meaning]}<br><b class='epd'>{i.root}</b> root. {i.root_meaning}"
                epd[root_meaning] = epd_string

            if root_meaning not in epd.keys():
                epd_string = f"<b class='epd'>{i.root}</b> root. {i.root_meaning}"
                epd.update({root_meaning: epd_string})

    epd_data_list: List[DictEntry] = []

    for counter, (word, html_string) in enumerate(epd.items()):
        html = ""
        html += "<body>"
        html += f"<div class ='dpd'><p>{html_string}</p></div>"
        html += "</body></html>"

        size_dict["epd"] += len(html)
        size_dict["epd_header"] += len(squash_whitespaces(header))

        html = squash_whitespaces(header) + minify(html)

        res = DictEntry(
            word=word,
            definition_html=html,
            definition_plain="",
            synonyms=[],
        )

        epd_data_list.append(res)

    pr.yes(len(epd_data_list))

    return epd_data_list, size_dict


def extract_sutta_numbers(meaning_2):
    # Extract sutta number from i.meaning_2
    unified_pattern = r"\(([A-Z]+)\s?([\d\.]+)(-\d+)?\)|([A-Z]+)[\s]?([\d\.]+)(-\d+)?"
    match = re.finditer(unified_pattern, meaning_2)
    combined_numbers = []

    for m in match:
        prefix = m.group(1) if m.group(1) else m.group(3)
        number = m.group(2) if m.group(2) else m.group(4)
        combined_number_without_space = (
            f"{prefix}{number}" if prefix and number else None
        )
        combined_number_with_space = f"{prefix} {number}" if prefix and number else None

        if "." in number:
            combined_number_with_colon_with_space = (
                f"{prefix} {number.replace('.', ':')}" if prefix and number else None
            )
            combined_number_with_colon_without_space = (
                f"{prefix}{number.replace('.', ':')}" if prefix and number else None
            )
        else:
            combined_number_with_colon_with_space = None
            combined_number_with_colon_without_space = None

        combined_numbers.extend(
            [
                combined_number_without_space,
                combined_number_with_space,
                combined_number_with_colon_with_space,
                combined_number_with_colon_without_space,
            ]
        )

    return combined_numbers


def update_epd(epd, combined_numbers, i, make_link=True):
    # Use sutta number as key in epd
    for combined_number in combined_numbers:
        if combined_number:
            number_link = i.source_link_sutta
            if make_link and number_link:
                anchor_link = f'<a class="link" href="{number_link}">link</a>'
                epd_string = (
                    f"<b class='epd'>{i.lemma_clean}</b>. {i.meaning_2} {anchor_link}"
                )
            else:
                epd_string = f"<b class='epd'>{i.lemma_clean}</b>. {i.meaning_2}"

            if combined_number in epd.keys():
                epd[combined_number] += f"<br>{epd_string}"
            else:
                epd.update({combined_number: epd_string})


if __name__ == "__main__":
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    generate_epd_html(db_session, pth)
