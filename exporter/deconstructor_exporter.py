#!/usr/bin/env python3

"""Export Deconstrutor To GoldenDict and MDict formats."""

import os
import sys

from functools import reduce
from pathlib import Path
from typing import List, Dict

from css_html_js_minify import css_minify
from rich import print
from mako.template import Template
from minify_html import minify

from mdict_exporter import mdict_synonyms
from db.models import Sandhi
from db.get_db_session import get_db_session

from tools.goldendict_path import goldedict_path
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc, bip, bop
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.configger import config_test
from helpers import TODAY
from tools.writemdict.writemdict import MDictWriter

sys.path.insert(1, 'tools/writemdict')

def main():
    tic()
    print("[bright_yellow]making dpd deconstructor for goldendict & mdict")
    
    # check config
    if config_test("dictionary", "make_mdict", "yes"):
        make_mdct: bool = True
    else:
        make_mdct: bool = False

    if config_test("goldendict", "copy_unzip", "yes"):
        copy_unzip: bool = True
    else:
        copy_unzip: bool = False

    pth = ProjectPaths()
    sandhi_data_list = make_sandhi_data_list(pth)
    make_golden_dict(pth, sandhi_data_list)

    if copy_unzip:
        unzip_and_copy(pth)

    if make_mdct:
        make_mdict(pth, sandhi_data_list)

    toc()


def make_sandhi_data_list(pth: ProjectPaths):
    """Prepare data set for GoldenDict of sandhi, splits and synonyms."""

    print(f"[green]{'making sandhi data list':<40}")
    db_session = get_db_session(pth.dpd_db_path)
    sandhi_db = db_session.query(Sandhi).all()
    sandhi_db_length: int = len(sandhi_db)
    SANDHI_CONTRACTIONS: dict = make_sandhi_contraction_dict(db_session)
    sandhi_data_list: list = []

    with open(pth.sandhi_css_path) as f:
        sandhi_css = f.read()
        sandhi_css = css_minify(sandhi_css)

    header_templ = Template(filename=str(pth.header_deconstructor_templ_path))
    sandhi_header = str(header_templ.render(css=sandhi_css, js=""))

    sandhi_templ = Template(filename=str(pth.sandhi_templ_path))

    bip()
    for counter, i in enumerate(sandhi_db):
        splits = i.split_list

        html_string: str = sandhi_header
        html_string += "<body>"
        html_string += str(sandhi_templ.render(
            i=i,
            splits=splits,
            today=TODAY))

        html_string += "</body></html>"
        html_string = minify(html_string)

        # make synonyms list
        synonyms = add_niggahitas([i.sandhi])
        synonyms += i.sinhala_list
        synonyms += i.devanagari_list
        synonyms += i.thai_list
        if i.sandhi in SANDHI_CONTRACTIONS:
            contractions = SANDHI_CONTRACTIONS[i.sandhi]["contractions"]
            synonyms.extend(contractions)

        sandhi_data_list += [{
            "word": i.sandhi,
            "definition_html": html_string,
            "definition_plain": "",
            "synonyms": synonyms}]

        if counter % 50000 == 0:
            print(
                f"{counter:>10,} / {sandhi_db_length:<10,} {i.sandhi[:20]:<20} {bop():>10}")
            bip()

    return sandhi_data_list


def make_golden_dict(pth, sandhi_data_list):

    print(f"[green]{'generating goldendict':<22}", end="")
    zip_path = pth.deconstructor_zip_path

    ifo = ifo_from_opts({
        "bookname": "DPD Deconstructor",
        "author": "Bodhirasa",
        "description": "Automated compound deconstruction and sandhi-splitting of all words in Chaṭṭha Saṅgāyana Tipitaka and Sutta Central texts.",
        "website": "https://digitalpalidictionary.github.io/"
        })

    export_words_as_stardict_zip(sandhi_data_list, ifo, zip_path)

    print(f"{len(sandhi_data_list):,}")


def unzip_and_copy(pth):

    local_goldendict_path: (Path |str) = goldedict_path()

    if (
        local_goldendict_path and 
        local_goldendict_path.exists()
        ):
        print(f"[green]unzipping and copying to [blue]{local_goldendict_path}")
        os.popen(
            f'unzip -o {pth.deconstructor_zip_path} -d "{local_goldendict_path}"')
    else:
        print("[red]local GoldenDict directory not found")


def make_mdict(pth, sandhi_data_list: List[Dict]):
    """Export to MDict format."""

    print(f"[green]{'exporting mdct':<22}")

    bip()
    print("[white]adding 'mdict' and h3 tag", end=" ")
    for i in sandhi_data_list:
        i['definition_html'] = i['definition_html'].replace(
            "GoldenDict", "MDict")
        i['definition_html'] = f"<h3>{i['word']}</h3>{i['definition_html']}"
    print(bop())

    bip()
    print("[white]reducing synonyms", end=" ")
    sandhi_data = reduce(mdict_synonyms, sandhi_data_list, [])
    print(bop())

    bip()
    print("[white]writing mdict", end=" ")
    description = """<p>DPD Deconstructor by Bodhirasa</p>
<p>For more infortmation, please visit
<a href=\"https://digitalpalidictionary.github.io\">
the Digital Pāḷi Dictionary website</a></p>"""

    writer = MDictWriter(
        sandhi_data,
        title="DPD Deconstructor",
        description=description)
    print(bop())

    bip()
    print("[white]copying mdx file", end=" ")
    with open(pth.deconstructor_mdict_mdx_path, "wb") as outfile:
        writer.write(outfile)
    print(bop())


if __name__ == "__main__":
    main()
