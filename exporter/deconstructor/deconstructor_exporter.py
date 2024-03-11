#!/usr/bin/env python3

"""Export Deconstrutor To GoldenDict and MDict formats."""

import os
import sys

from pathlib import Path
from typing import List, Dict

from css_html_js_minify import css_minify
from mako.template import Template
from minify_html import minify
from rich import print
from exporter.goldendict.helpers import TODAY

from db.get_db_session import get_db_session
from db.models import Lookup

from tools.configger import config_test
from tools.goldendict_path import goldedict_path
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc, bip, bop


sys.path.insert(1, 'tools/writemdict')

class Metadata:
    """Metadata for Dictionary Info file."""
    title: str = "DPD Deconstructor"
    author: str = "Bodhirasa"
    description: str = "<h3>DPD Deconstructor by Bodhirasa</h3><p>Automated compound deconstruction and sandhi-splitting of all words in <b>Chaṭṭha Saṅgāyana Tipitaka</b> and <b>Sutta Central</b> texts.</p><p>For more information please visit the <a href='https://digitalpalidictionary.github.io/deconstructor.html'>Deconstrutor page</a> on the <a href='https://digitalpalidictionary.github.io/'>DPD website</a>.</p>"
    website: str = "https://digitalpalidictionary.github.io/"


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
        if config_test("goldendict", "copy_unzip", "yes"):
            copy_unzip: bool = True
        else:
            copy_unzip: bool = False

        pth = ProjectPaths()
        m = Metadata()
        decon_data_list = make_decon_data_list(pth)
        make_golden_dict(pth, decon_data_list, m)

        if copy_unzip:
            unzip_and_copy(pth)

        if make_mdct:
            make_mdict(pth, decon_data_list, m)
      
    else:
        print("generating is disabled in the config")
    toc()
    

def make_decon_data_list(pth: ProjectPaths):
    """Prepare data set for GoldenDict of deconstructions and synonyms."""

    print(f"[green]{'making deconstructor data list':<40}")

    db_session = get_db_session(pth.dpd_db_path)
    decon_db = db_session.query(Lookup).filter(Lookup.deconstructor!="").all()
    decon_db_length: int = len(decon_db)
    sandhi_contractions: dict = make_sandhi_contraction_dict(db_session)
    decon_data_list: list = []

    with open(pth.deconstructor_css_path) as f:
        decon_css = f.read()
        decon_css = css_minify(decon_css)

    header_templ = Template(filename=str(pth.header_deconstructor_templ_path))
    decon_header = str(header_templ.render(css=decon_css, js=""))

    decon_templ = Template(filename=str(pth.deconstructor_templ_path))

    bip()
    for counter, i in enumerate(decon_db):
        deconstructions = i.deconstructor_unpack

        html_string: str = decon_header
        html_string += "<body>"
        html_string += str(decon_templ.render(
            i=i,
            deconstructions=deconstructions,
            today=TODAY))

        html_string += "</body></html>"
        html_string = minify(html_string)

        # make synonyms list
        synonyms = add_niggahitas([i.lookup_key], all=False)
        synonyms.extend(i.sinhala_unpack)
        synonyms.extend(i.devanagari_unpack)
        synonyms.extend(i.thai_unpack)
        if i.lookup_key in sandhi_contractions:
            contractions = sandhi_contractions[i.lookup_key]["contractions"]
            synonyms.extend(contractions)

        decon_data_list += [{
            "word": i.lookup_key,
            "definition_html": html_string,
            "definition_plain": "",
            "synonyms": synonyms}]

        if counter % 50000 == 0:
            print(
                f"{counter:>10,} / {decon_db_length:<10,} {i.lookup_key[:20]:<20} {bop():>10}")
            bip()

    return decon_data_list


def make_golden_dict(pth, decon_data_list, m: Metadata):
    """Export GoldenDict."""
    print(f"[green]{'generating goldendict':<22}", end="")
    zip_path = pth.deconstructor_zip_path


    ifo = ifo_from_opts({
        "bookname": m.title,
        "author": m.author,
        "description": m.description,
        "website": m.website
        })

    export_words_as_stardict_zip(decon_data_list, ifo, zip_path)

    print(f"{len(decon_data_list):,}")


def unzip_and_copy(pth):
    """Unzip and copy GoldenDict to a local folder."""
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


def make_mdict(pth, decon_data_list: List[Dict], m: Metadata):
    """Export MDict."""

    print(f"[green]{'exporting mdct':<22}")

    export_to_mdict(
        decon_data_list,
        pth.deconstructor_mdict_mdx_path,
        m.title,
        m.description)


if __name__ == "__main__":
    main()