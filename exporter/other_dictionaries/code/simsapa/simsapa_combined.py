"""Extract PTS PED from Simsapa.
Export to GoldenDict, MDict and JSON."""

import sqlite3

from bs4 import BeautifulSoup

from tools.configger import config_read
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.printer import p_title, p_green, p_yes


class ProgData():
    pth = ProjectPaths()
    simsapa_db_path = config_read("simsapa", "db_path")
    simsapa_db: list[tuple[str, str, str]]
    dict_data: list[DictEntry]


def extract_simsapa_db_data(g: ProgData):
    """Query Simsapa DB for dict data
    - 1. Nyanatiloka's Buddhist Dictionary
    - 3. Dictionary of Pali Proper Names (DPPN)
    - 10. New Concise Pali - English Dictionary (NCPED)
    - 11. Pali Text Society Pali - English Dictionary (PTS)."""
    
    p_green("querying simspa db")

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
    p_yes(len(simsapa_db))


def make_data_list(g: ProgData):
    p_green("making data list")
    dict_data: list[DictEntry] = []
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

            dict_entry = DictEntry(
                word = headword,
                definition_html = html_comp,
                definition_plain = "",
                synonyms = list(synonyms_comp)
            )
            dict_data.append(dict_entry)

    g.dict_data = dict_data
    p_yes(len(dict_data))


def save_goldendict_and_mdict(g: ProgData):
    """Save as Goldendict"""
    
    dict_info = DictInfo(
        bookname = "Simsapa Combined Pali-English Dictionary",
        author = "",
        description = "<h3>Simsapa Combined Pali-English Dictionary</h3><p>Nyanatiloka's Buddhist Dictionary</p><p>Dictionary of Pali Proper Names (DPPN)</p><p>New Concise Pali - English Dictionary (NCPED)</p><p>Pali Text Society Pali - English Dictionary (PTS)</p><p>Reformatted for the <a href='https://github.com/simsapa/simsapa'>Simsapa Dhamma Reader.</a></p><p>Encoded by Bodhirasa 2024.</p>",
        website = "https://simsapa.github.io/",
        source_lang = "pa",
        target_lang = "en",
    )
    
    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = g.pth.simsapa_gd_path,
        md_path = g.pth.simsapa_mdict_path,
        dict_name= "simsapa",
        icon_path = None,
        zip_up = True,
        delete_original = True
    )

    # save goldendict
    export_to_goldendict_with_pyglossary(
        dict_info, 
        dict_vars,
        g.dict_data,
    )

    # save as mdict
    export_to_mdict(
        dict_info, 
        dict_vars,
        g.dict_data
    )


def main():
    tic()
    p_title("exporting Simsapa Combined to GoldenDict and MDict")
    g = ProgData()
    extract_simsapa_db_data(g)
    make_data_list(g)
    save_goldendict_and_mdict(g)
    toc()

if __name__ == "__main__":
    main()

