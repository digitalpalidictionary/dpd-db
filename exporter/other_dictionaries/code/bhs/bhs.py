#!/usr/bin/env python3

from bs4 import BeautifulSoup
from rich import print

from tools.sanskrit_translit import slp1_translit
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary


def main():
    tic()
    print("[bright_yellow]exporting Edgerton BHS to various formats")
    print("[green]preparing data")
    pth = ProjectPaths()
    
    dict_data: list[DictEntry] = []

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

            dict_entry = DictEntry(
                word = headword,
                definition_html = html,
                definition_plain = "",
                synonyms = [])
            dict_data.append(dict_entry)

    # save as goldendict
    print("[green]saving goldendict")

    dict_info = DictInfo(
        bookname = "Edgerton's Buddhist Hybrid Sanskrit Dictionary 1953",
        author = "Franklin Edgerton",
        description = """<h3>Buddhist Hybrid Sanskrit grammar and dictionary</h3><p>by Franklin Edgerton, Serling Professor of Sanskrit and Comparative Philology, Yale University.<p><b>Volume II: Dictionary</b></p><p>Yale University Press. New Haven, Conn. 1953.</p><p>For more Sanskrit dictionaries please visit <a href="http://www.sanskrit-lexicon.uni-koeln.de">Cologne Sanskrit Lexicon</a> website.</p><p>Encoded by Bodhirasa 2024.</p>""",
        website = "www.sanskrit-lexicon.uni-koeln.de",
        source_lang = "sa",
        target_lang = "en"
    )

    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = pth.bhs_gd_path,
        md_path = pth.bhs_mdict_path,
        dict_name= "bhs",
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
        dict_data,
    )
       
    toc()

if __name__ == "__main__":
    main()