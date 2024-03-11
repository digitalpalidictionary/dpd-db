"""Export Crital Pāḷi dictionary into GoldenDict, MDict and JSON formats."""

import re
import json

from rich import print

from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc

def clean_text(text):
    """Clean up problems in the source text."""
    text = text \
        .replace("I", "l") \
        .replace("<br\\/>", " ") \
        .replace("rh", "ṁ") \
        .replace("ç", "ś") \
        .replace("ṁ", "ṃ")
    text = text.replace("  ", " ")
    
    # replace end tags with no spaces after
    text = re.sub(r"([a-zāūīṅñṭḍṇḷ]<\/.>)([a-zāūīṅñṭḍṇḷ])", "\\1 \\2", text)
    return text


def main():
    tic()
    print("[bright_yellow]exporting cpd into various formats")
    
    pth = ProjectPaths()

    # make data list
    print("[green]making data list")
    with open(pth.cpd_source_path, "r") as file:
        cped_data = json.load(file)

    cpd_data_list = []
    for i in cped_data:
        headword, html, id = i
        headword = clean_text(headword)
        html = clean_text(html)

        if "ṃ" in headword:
            synoyms = add_niggahitas([headword])
        else:
            synoyms = []

        cpd_data_list.append({
            "word": headword, 
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synoyms            
            })
    
    # sort into pali alphabetical order
    cpd_data_list = sorted(cpd_data_list, key=lambda x: pali_sort_key(x["word"]))

    # save as json
    print("[green]saving json")
    with open(pth.cpd_json_path, "w") as file:
        json.dump(cpd_data_list, file, indent=4, ensure_ascii=False)

    # save as goldendict
    print("[green]saving goldendict")  
    
    bookname = "Critical Pāli Dictionary"
    author = "V. Trenckner et al."
    description = "<h3>A Critical Pāli Dictionary</h3><p>by V. Trenckner, et al. Published by the Royal Danish Academy of Science and Letters, Copenhagen, 1925 -2011</p>The dictionary can be found online on the <a href='https://cpd.uni-koeln.de'>Cologne University</a> website</p><p>Encoded by Bodhirasa 2024.</p>"
    website = "https://cpd.uni-koeln.de"

    ifo = ifo_from_opts({
            "bookname": bookname,
            "author": author,
            "description": description,
            "website": website,
        })

    export_words_as_stardict_zip(cpd_data_list, ifo, pth.cpd_gd_path)

    # save as mdict
    print("[green]saving mdict")
    output_path = str(pth.cpd_mdict_path)

    export_to_mdict(
        cpd_data_list,
        output_path,
        bookname,
        description)

    toc()

if __name__ == "__main__":
    main()