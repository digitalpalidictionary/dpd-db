"""Compile HTML data for English to Pāḷi dictionary."""

import re

from css_html_js_minify import css_minify
from mako.template import Template
from minify_html import minify
from rich import print
from sqlalchemy.orm import Session
from typing import List, Tuple

from export_dpd import render_header_templ

from db.models import PaliWord, PaliRoot
from tools.tic_toc import bip, bop
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.link_generator import generate_link
from tools.configger import config_test
from tools.utils import RenderResult, RenderedSizes, default_rendered_sizes


def generate_epd_html(db_session: Session, pth: ProjectPaths) -> Tuple[List[RenderResult], RenderedSizes]:
    """generate html for english to pali dictionary"""

    size_dict = default_rendered_sizes()

    print("[green]generating epd html")

    # check config
    if config_test("dictionary", "make_link", "yes"):
        make_link: bool = True
    else:
        make_link: bool = False

    dpd_db: list = db_session.query(PaliWord).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))
    dpd_db_length = len(dpd_db)

    roots_db: list = db_session.query(PaliRoot).all()
    roots_db_length = len(roots_db)

    epd: dict = {}
    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]

    with open(pth.epd_css_path) as f:
        epd_css: str = f.read()

    epd_css = css_minify(epd_css)

    header_templ = Template(filename=str(pth.header_templ_path))
    header = render_header_templ(
        pth, css=epd_css, js="", header_templ=header_templ)

    bip()
    for counter, i in enumerate(dpd_db):
        meanings_list = []
        i.meaning_1 = re.sub(r"\?\?", "", i.meaning_1)

        if (i.meaning_1 and
                i.pos not in pos_exclude_list):

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
                    epd_string = f"{epd[meaning]}<br><b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1}"
                    epd[meaning] = epd_string

                if meaning in epd.keys() and i.plus_case:
                    epd_string = f"{epd[meaning]}<br><b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1} ({i.plus_case})"
                    epd[meaning] = epd_string

                if meaning not in epd.keys() and not i.plus_case:
                    epd_string = f"<b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1}"
                    epd.update(
                        {meaning: epd_string})

                if meaning not in epd.keys() and i.plus_case:
                    epd_string = f"<b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1} ({i.plus_case})"
                    epd.update(
                        {meaning: epd_string})

        # Extract sutta number from i.meaning_2 and use it as key in epd
        if i.family_set.startswith("suttas of") and i.meaning_2:
            sutta_number_match = re.search(r"\(([A-Z]+)[\s]?([\d\.]+)\)", i.meaning_2)
            if sutta_number_match:
                prefix = sutta_number_match.group(1)
                number = sutta_number_match.group(2)

                sutta_number_no_space = f"{prefix}{number}"  # Format without space
                sutta_number_with_space = f"{prefix} {number}"  # Format with space

                for sutta_number in [sutta_number_no_space, sutta_number_with_space]:
                    if make_link is True:
                        # Generate link for the sutta number
                        sutta_link = generate_link(sutta_number)
                        anchor_link = f'<a href="{sutta_link}">link</a>'
                        
                        if sutta_number in epd.keys():
                            # Append the new sutta name to the existing value
                            epd[sutta_number] += f"<br><b class='epd'>{i.pali_clean}</b>. {i.meaning_2} {anchor_link}"
                        else:
                            # Create a new key-value pair in epd
                            epd_string = f"<b class='epd'>{i.pali_clean}</b>. {i.meaning_2} {anchor_link}"
                            epd.update({sutta_number: epd_string})
                    else:
                        if sutta_number in epd.keys():
                            # Append the new sutta name to the existing value
                            epd[sutta_number] += f"<br><b class='epd'>{i.pali_clean}</b>. {i.meaning_2}"
                        else:
                            # Create a new key-value pair in epd
                            epd_string = f"<b class='epd'>{i.pali_clean}</b>. {i.meaning_2}"
                            epd.update({sutta_number: epd_string})


        # bhikkhupatimokkha rules names
        if i.family_set == "bhikkhupātimokkha rules" and i.meaning_2:
            # Use regex to capture both formats with and without space
            rule_number_match = re.search(r"([A-Z]+)[\s]?([\d]+)", i.meaning_2)
            
            if rule_number_match:
                    prefix = rule_number_match.group(1)
                    number = rule_number_match.group(2)
                    
                    rule_number_no_space = f"{prefix}{number}"  # Format without space
                    rule_number_with_space = f"{prefix} {number}"  # Format with space

                    for rule_number in [rule_number_no_space, rule_number_with_space]:

                        if make_link is True:
                            # Generate link for the rule number
                            rule_link = generate_link(rule_number)
                            anchor_link = f'<a href="{rule_link}">link</a>'

                            if rule_number in epd.keys():
                                # Append the new sutta name to the existing value
                                epd[rule_number] += f"<br><b class='epd'>{i.pali_clean}</b>. {i.meaning_2} {anchor_link}"
                            else:
                                # Create a new key-value pair in epd
                                epd_string = f"<b class='epd'>{i.pali_clean}</b>. {i.meaning_2} {anchor_link}"
                                epd.update({rule_number: epd_string})

                        else:
                            if rule_number in epd.keys():
                                # Append the new sutta name to the existing value
                                epd[rule_number] += f"<br><b class='epd'>{i.pali_clean}</b>. {i.meaning_2}"
                            else:
                                # Create a new key-value pair in epd
                                epd_string = f"<b class='epd'>{i.pali_clean}</b>. {i.meaning_2}"
                                epd.update({rule_number: epd_string})

        if counter % 10000 == 0:
            print(f"{counter:>10,} / {dpd_db_length:<10,} {i.pali_1[:20]:<20} {bop():>10}")
            bip()

    print("[green]adding roots to epd")

    for counter, i in enumerate(roots_db):

        root_meanings_list: list = i.root_meaning.split(", ")

        for root_meaning in root_meanings_list:
            if root_meaning in epd.keys():
                epd_string = f"{epd[root_meaning]}<br><b class = 'epd'>{i.root}</b> root. {i.root_meaning}"
                epd[root_meaning] = epd_string

            if root_meaning not in epd.keys():
                epd_string = f"<b class = 'epd'>{i.root}</b> root. {i.root_meaning}"
                epd.update(
                    {root_meaning: epd_string})

        if counter % 250 == 0:
            print(f"{counter:>10,} / {roots_db_length:<10,} {i.root:<20} {bop():>10}")
            bip()

    print("[green]compiling epd html")

    epd_data_list: List[RenderResult] = []

    for counter, (word, html_string) in enumerate(epd.items()):
        html = header
        size_dict["epd_header"] += len(header)

        html += "<body>"
        html += f"<div class ='epd'><p>{html_string}</p></div>"
        html += "</body></html>"
        size_dict["epd"] += len(html) - len(header)

        html = minify(html)

        res = RenderResult(
            word = word,
            definition_html = html,
            definition_plain = "",
            synonyms = [],
        )

        epd_data_list.append(res)

    return epd_data_list, size_dict
