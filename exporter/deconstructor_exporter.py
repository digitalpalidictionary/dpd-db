#!/usr/bin/env python3

"""Export Deconstrutor To GoldenDict and MDict formats."""

import os
import sys

from datetime import date
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

from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths as PTH
from tools.tic_toc import tic, toc, bip, bop
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts

sys.path.insert(1, 'tools/writemdict')
from writemdict import MDictWriter

sandhi_templ = Template(filename=str(PTH.sandhi_templ_path))
TODAY = date.today()


def main():
    tic()
    print("[bright_yellow]making dpd deconstructor for goldendict & mdict")
    sandhi_data_list = make_sandhi_data_list()
    make_golden_dict(PTH, sandhi_data_list)
    unzip_and_copy(PTH)
    make_mdict(PTH, sandhi_data_list)
    toc()


def make_sandhi_data_list():
    """Prepare data set for GoldenDict of sandhi, splits and synonyms."""

    print(f"[green]{'making sandhi data list':<40}")
    DB_SESSION = get_db_session("dpd.db")
    sandhi_db = DB_SESSION.query(Sandhi).all()
    sandhi_db_length: int = len(sandhi_db)
    SANDHI_CONTRACTIONS: dict = make_sandhi_contraction_dict(DB_SESSION)
    sandhi_data_list: list = []

    with open(PTH.sandhi_css_path) as f:
        sandhi_css = f.read()
        sandhi_css = css_minify(sandhi_css)

    header_tmpl = Template(filename=str(
        PTH.header_deconstructor_templ_path))
    sandhi_header = str(header_tmpl.render(css=sandhi_css, js=""))

    bip()
    for counter, i in enumerate(sandhi_db):
        splits = i.split_list

        html_string = sandhi_header
        html_string += "<body>"
        html_string += sandhi_templ.render(
            i=i,
            splits=splits,
            today=TODAY)

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


def make_golden_dict(PTH, sandhi_data_list):

    print(f"[green]{'generating goldendict':<22}", end="")
    zip_path = PTH.deconstructor_zip_path

    ifo = ifo_from_opts({
        "bookname": "DPD Deconstructor",
        "author": "Bodhirasa",
        "description": "Automated compound deconstruction and sandhi-splitting of all words in Chaṭṭha Saṅgāyana Tipitaka and Sutta Central texts.",
        "website": "https://digitalpalidictionary.github.io/"
        })

    export_words_as_stardict_zip(sandhi_data_list, ifo, zip_path)

    print(f"{len(sandhi_data_list):,}")


def unzip_and_copy(PTH):

    print(f"[green]{'unzipping and copying to goldendict dir':<22}")

    local_goldendict_path = Path("/home/bhikkhu/Documents/Golden Dict")
    if local_goldendict_path.exists():
        os.popen(
            f'unzip -o {PTH.deconstructor_zip_path} -d "/home/bhikkhu/Documents/Golden Dict"')
    else:
        print("[red]local GoldenDict directory not found")


def make_mdict(PTH: Path, sandhi_data_list: List[Dict]):
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
    outfile = open(PTH.deconstructor_mdict_mdx_path, 'wb')
    writer.write(outfile)
    outfile.close()
    print(bop())


if __name__ == "__main__":
    main()
