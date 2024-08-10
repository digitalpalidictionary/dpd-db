"""Export PEU into Goldendict, MDict and JSON formats."""

# the most up to date data is always available from 
# https://pm12e.pali.tools/dump

import json
import re
import sqlite3

from rich import print

from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
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


def extract_peu_from_data_dump():
    """Latest data from https://pm12e.pali.tools/dump"""

    with open("other_dictionaries/code/peu/source/peu_dump_2024_02_16.js") as f:
        raw_data = f.read()
        raw_data = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', raw_data)
        raw_data = raw_data.replace('"', '^^^')
        raw_data = raw_data.replace("'", '"')
        raw_data = raw_data.replace("^^^", "'")

        return json.loads(raw_data)



def main():
    tic()
    print("[bright_yellow]extracting peu data from TPR db")

    pth = ProjectPaths()
    peu_data = extract_peu_from_tpr_database()

    # peu_data_list = []
    dict_data: list[DictEntry] = []

    for i in peu_data:
        headword, html, book_id = i
        headword = headword.replace("ṁ", "ṃ")
        html = html.replace("ṁ", "ṃ")
        
        if "ṃ" in headword:
            synonyms = add_niggahitas([headword])
        else:
            synonyms = []
        
        dict_entry = DictEntry(
            word = headword,
            definition_html = html,
            definition_plain = "",
            synonyms = synonyms
        )
        dict_data.append(dict_entry)

    # save as goldendict
    print("[green]saving goldendict")

    dict_info = DictInfo(
        bookname = "Pali English Ultimate",
        author = "Pali Myanmar Abhidhan",
        description = """<h3>Pali Myanmar Abhidhan</h3><p>Pali Myanmar Abhidhan is the world's largest Pali dictionary, a massive 23 volumes, with more than 200 000 words, a complete reference guide to the language of the root texts and commentaries.</p><p>There is a project underway to translate this into English, currently at about 80% human translated, the remainder is by Google.</p><p><a href='https://pm12e.pali.tools/'>Project Website</a></p><p>This dictionary can be found in the Tipitaka Pali Projector project on <a href='https://github.com/bksubhuti/Tipitaka-Pali-Projector'>Github</a></p><p>Encoded by Bodhirasa 2024.</p>""",
        website = "https://pm12e.pali.tools/",
        source_lang = "pa",
        target_lang = "en",
    )
    
    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = pth.peu_gd_path,
        md_path = pth.peu_mdict_path,
        dict_name= "peu",
        icon_path = None,
        zip_up=True,
        delete_original=True
    )

    export_to_goldendict_with_pyglossary(
        dict_info, 
        dict_vars,
        dict_data, 
        zip_synonyms=False
    )

    # save as mdict
    print("[green]saving mdict")

    export_to_mdict(
        dict_info, 
        dict_vars,
        dict_data
    )

    toc()


if __name__ == "__main__":
    main()
