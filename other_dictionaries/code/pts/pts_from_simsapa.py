"""Extract PTS PED from Simsapa.
Export to GoldenDict, MDict and JSON."""

import json
import sqlite3
from bs4 import BeautifulSoup

from rich import print

from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc


def extract_pts_from_simsapa():
    """Query Simsapa DB for PTS data."""
    print("[green]querying simspa db")

    simsapa_db_path = "../../.local/share/simsapa/assets/appdata.sqlite3"
    conn = sqlite3.connect(simsapa_db_path)
    c = conn.cursor()
    c.execute("""SELECT word, definition_html, synonyms FROM dict_words WHERE source_uid is 'pts'""")
    pts_data = c.fetchall()

    return pts_data

def main():
    tic()
    print("[bright_yellow]exporting PTS to GoldenDict, MDict and JSON")

    pth = ProjectPaths()
    pts_data = extract_pts_from_simsapa()

    print("[green]making data list")
    pts_data_list = []
    for i in pts_data:
        headword, html, synonyms = i

        soup = BeautifulSoup(html, "html.parser")

		# remove all the "pb" tags
        ays = soup.find_all("a")
        for ay in ays:
            ay.unwrap()

        html = str(soup)

        headword = headword.replace("ṁ", "ṃ")
        html = html.replace("ṁ", "ṃ")

        if "ṃ" in headword:
            synonyms = add_niggahitas([headword], all=False)
        else:
            synonyms = []

        pts_data_list.append({
            "word": headword, 
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms           
            })

    # sort into sanskrit alphabetical order
    pts_data_list = sorted(pts_data_list, key=lambda x: pali_sort_key(x["word"]))

    # save as json
    print("[green]saving json")
    with open(pth.pts_json_path, "w") as file:
        json.dump(pts_data_list, file, indent=4, ensure_ascii=False)

    # save as goldendict
    print("[green]saving goldendict")

    # TODO find out more details, website etc

    bookname = "PTS Pali-English Dictionary"
    description = "The Pali Text Society's Pali-English Dictionary 1925"
    author = "T.W. Rhys Davids & William Stede"
    website = ""

    ifo = ifo_from_opts({
            "bookname": bookname,
            "author": author,
            "description": description,
            "website": website
            })

    export_words_as_stardict_zip(pts_data_list, ifo, pth.pts_gd_path)

    # save as mdict
    print("[green]saving mdict")
    output_file = str(pth.pts_mdict_path)
    
    export_to_mdict(
        pts_data_list,
        output_file,
        bookname,
        description)

    toc()


if __name__ == "__main__":
    main()

