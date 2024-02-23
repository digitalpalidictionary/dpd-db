"""Extract PTS PED from Simsapa.
Export to GoldenDict, MDict and JSON."""

import json
import sqlite3

from bs4 import BeautifulSoup
from rich import print

from tools.configger import config_read
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc


class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.simsapa_db_path = config_read("simsapa", "db_path")
        self.simsapa_db: list[tuple[str, str, str]]
        self.simsapa_data_list: list[dict[str, str]]

        self.bookname = "Simsapa Combined Pali-English Dictionary"
        self.author = ""
        self.description = "<h3>Simsapa Combined Pali-English Dictionary</h3><p>Nyanatiloka's Buddhist Dictionary</p><p>Dictionary of Pali Proper Names (DPPN)</p><p>New Concise Pali - English Dictionary (NCPED)</p><p>Pali Text Society Pali - English Dictionary (PTS)</p><p>Reformatted for the <a href='https://github.com/simsapa/simsapa'>Simsapa Dhamma Reader.</a></p><p>Encoded by Bodhirasa 2024.</p>"
        self.website = "https://simsapa.github.io/"


def extract_simsapa_db_data(g: ProgData):
    """Query Simsapa DB for dict data
    - 1. Nyanatiloka's Buddhist Dictionary
    - 3. Dictionary of Pali Proper Names (DPPN)
    - 10. New Concise Pali - English Dictionary (NCPED)
    - 11. Pali Text Society Pali - English Dictionary (PTS)."""
    
    print("[green]querying simspa db")

    if g.simsapa_db_path:
        conn = sqlite3.connect(g.simsapa_db_path)
        c = conn.cursor()
        c.execute(
            """
            SELECT word, definition_html, synonyms
            FROM dict_words
            WHERE dictionary_id IN (1, 3, 10, 11)""")
        simsapa_db = c.fetchall()

        # sort by pali alphabetical
        simsapa_db = sorted(simsapa_db, key=lambda x: pali_sort_key(x[0]))

    g.simsapa_db = simsapa_db

def main():
    tic()
    print("[bright_yellow]exporting Simsapa Combined to GoldenDict, MDict and JSON")
    g = ProgData()
    extract_simsapa_db_data(g)
    make_data_list(g)
    save_json(g)
    save_goldendict(g)
    save_mdict(g)
    toc()


def make_data_list(g: ProgData):

    print("[green]making data list")
    simsapa_data_list = []
    processed_headwords = set()

    index = 0
    for index, data_tuple in enumerate(g.simsapa_db):
        headword, html, synonyms = data_tuple
        
        if headword not in processed_headwords:
            processed_headwords.add(headword)

            html_comp = html
            if synonyms:
                synonyms_comp = set([synonyms])
            else:
                synonyms_comp = set()
            if index +1 < len(g.simsapa_db):
                next_index = index + 1
                next_headword = g.simsapa_db[next_index][0]
            else:
                next_headword = "fin"

            # combine the data of identical headwords
            while headword == next_headword:
                headword, html, synonyms = g.simsapa_db[next_index]
                html_comp += html
                if synonyms:
                    synonyms_comp.add(synonyms)
                next_index = next_index + 1
                next_headword = g.simsapa_db[next_index][0]

            # remove all the "a" tags
            soup = BeautifulSoup(html_comp, "html.parser")
            ays = soup.find_all("a")
            for ay in ays:
                ay.unwrap()

            # normalize niggahitas and add to synonyms
            html_comp = str(soup)
            html_comp = html_comp.replace("ṁ", "ṃ")
            
            headword = headword.replace("ṁ", "ṃ")
            if "ṃ" in headword:
                synonyms_comp.update(add_niggahitas([headword], all=False))

            simsapa_data_list.append({
                "word": headword, 
                "definition_html": html_comp,
                "definition_plain": "",
                "synonyms": list(synonyms_comp)           
                })

    # sort into pali alphabetical order
    simsapa_data_list = sorted(simsapa_data_list, key=lambda x: pali_sort_key(x["word"]))
    g.simsapa_data_list = simsapa_data_list


def save_json(g: ProgData):
    """save as json"""
    print("[green]saving json")
    
    with open(g.pth.simsapa_json_path, "w") as file:
        json.dump(g.simsapa_data_list, file, indent=4, ensure_ascii=False)


def save_goldendict(g: ProgData):
    """Save as Goldendict"""
    print("[green]saving goldendict")

    ifo = ifo_from_opts({
            "bookname": g.bookname,
            "author": g.author,
            "description": g.description,
            "website": g.website
            })

    export_words_as_stardict_zip(g.simsapa_data_list, ifo, g.pth.simsapa_gd_path) #type:ignore


def save_mdict(g: ProgData):
    """Save as mdict"""
    print("[green]saving mdict")

    output_file = str(g.pth.simsapa_mdict_path)
    
    export_to_mdict(
        g.simsapa_data_list,
        output_file,
        g.bookname,
        g.description)


if __name__ == "__main__":
    main()

