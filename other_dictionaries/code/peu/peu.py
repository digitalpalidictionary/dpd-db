"""Export PEU into Goldendict, MDict and JSON formats."""

import json
import sqlite3

from rich import print
from pathlib import Path

from tools.date_and_time import year_month_day_dash
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc



def extract_peu_from_tpr_database():
    """Query TPR db for PEU data"""
    print("[green]querying tpr db")

    tpr_db_path = "../../.local/share/tipitaka_pali_reader/tipitaka_pali.db"
    
    # PEU is in the dictionary table with book_id = 8
    conn = sqlite3.connect(tpr_db_path)
    c = conn.cursor()
    c.execute("""SELECT * FROM dictionary WHERE book_id = 8""")
    peu_data = c.fetchall()

    return peu_data


def main():
    tic()
    print("[bright_yellow]extracting peu data from tpr db")

    pth = ProjectPaths()
    peu_data = extract_peu_from_tpr_database()

    peu_data_list = []
    for i in peu_data:
        headword, html, book_id = i
        headword = headword.replace("ṁ", "ṃ")
        html = html.replace("ṁ", "ṃ")
        
        if "ṃ" in headword:
            synonyms = add_niggahitas([headword])
        else:
            synonyms = []

        peu_data_list.append({
            "word": headword, 
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms            
            })

    # sort into pali alphabetical order
    peu_data_list = sorted(peu_data_list, key=lambda x: pali_sort_key(x["word"]))

    # save as json
    print("[green]saving json")
    with open(pth.peu_json_path, "w") as file:
        json.dump(peu_data_list, file, indent=4, ensure_ascii=False)

    # save as goldendict
    print("[green]saving goldendict")

    # TODO find out more details, website etc

    bookname = "Pāḷi Myanmar Abhidhan"
    author = "Pāḷi Myanmar Abhidhan"
    description = f"Pāḷi Myanmar Abhidhan, translated into English. Version {year_month_day_dash()}"
    website = ""

    ifo = ifo_from_opts({
            "bookname": bookname,
            "author": author,
            "description": description,
            "website": website
            })

    export_words_as_stardict_zip(peu_data_list, ifo, pth.peu_gd_path)

    # save as mdict
    print("[green]saving mdict")
    output_path = str(pth.peu_mdict_path)

    export_to_mdict(
        peu_data_list,
        output_path,
        bookname,
        f"{description}. {website}")

    toc()


if __name__ == "__main__":
    main()
