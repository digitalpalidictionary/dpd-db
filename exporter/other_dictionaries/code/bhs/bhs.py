#!/usr/bin/env python3

import json

from bs4 import BeautifulSoup
from rich import print

from tools.sanskrit_translit import slp1_translit
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import sanskrit_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]exporting edgerton bhs to various formats")
    print("[green]preparing data")
    pth = ProjectPaths()
    
    bhs_data_list = []

    with open(pth.bhs_source_path) as f:
        soup = BeautifulSoup(f, "xml")
        h1s = soup.find_all("H1")
        for h1 in h1s:
            headword = slp1_translit(h1.key1.text)

            lbs = h1.find_all("div")
            for lb in lbs:
                lb.unwrap()

            html = str(h1.body)
            html = html.replace("¦", "")

            if "ṃ" in headword:
                synonyms = add_niggahitas([headword], all=False)
                synonyms.remove(headword)
            else:
                synonyms = []

            bhs_data_list.append({
                "word": headword,
                "definition_html": html,
                "definition_plain": "",
                "synonyms": synonyms
            })

    # sort into sanskrit alphabetical order
    bhs_data_list = sorted(bhs_data_list, key=lambda x: sanskrit_sort_key(x["word"]))

    # save as json
    print("[green]saving json")
    with open(pth.bhs_json_path, "w") as file:
        json.dump(bhs_data_list, file, indent=4, ensure_ascii=False)

    # save as goldendict
    print("[green]saving goldendict")

    bookname = "Edgerton's Buddhist Hybrid Sanskrit Dictionary 1953"
    author = "Franklin Edgerton"
    description = """<h3>Buddhist Hybrid Sanskrit grammar and dictionary</h3><p>by Franklin Edgerton, Serling Professor of Sanskrit and Comparative Philology, Yale University.<p><b>Volume II: Dictionary</b></p><p>Yale University Press. New Haven, Conn. 1953.</p><p>For more Sanskrit dicitonaries please visit <a href="http://www.sanskrit-lexicon.uni-koeln.de">Cologne Sanskrit Lexicon</a> website.</p><p>Encoded by Bodhirasa 2024.</p>"""
    website = "www.sanskrit-lexicon.uni-koeln.de"

    ifo = ifo_from_opts(
        {
            "bookname": bookname,
            "author": author,
            "description": description,
            "website": website,
        }
    )

    export_words_as_stardict_zip(
        bhs_data_list, ifo, pth.bhs_gd_path)

    # save as mdict
    print("[green]saving mdict")
    output_file = str(pth.bhs_mdict_path)
    
    export_to_mdict(
        bhs_data_list,
        output_file,
        bookname,
        description,
        h3_header=True
        )

    toc()

if __name__ == "__main__":
    main()