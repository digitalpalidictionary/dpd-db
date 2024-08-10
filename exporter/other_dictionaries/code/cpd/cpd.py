"""Export Crital Pāḷi dictionary into GoldenDict, MDict and JSON formats."""

import re
import json

from rich import print

from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
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
    print("[bright_yellow]exporting CPD for GoldenDict and MDict")
    
    pth = ProjectPaths()

    # make data list
    print("[green]making data list")
    with open(pth.cpd_source_path, "r") as file:
        cped_data = json.load(file)

    dict_data: list[DictEntry] = []
    for i in cped_data:
        headword, html, id = i
        headword = clean_text(headword)
        html = clean_text(html)

        if "ṃ" in headword:
            synonyms = add_niggahitas([headword])
        else:
            synonyms = []
        
        dict_entry = DictEntry(
            word = headword,
            definition_html = html,
            definition_plain = "",
            synonyms = synonyms)
        dict_data.append(dict_entry)

    # save as goldendict
    print("[green]saving goldendict")

    dict_info = DictInfo(
        bookname = "Critical Pāli Dictionary",
        author = "V. Trenckner et al.",
        description = "<h3>A Critical Pāli Dictionary</h3><p>by V. Trenckner, et al. Published by the Royal Danish Academy of Science and Letters, Copenhagen, 1925 -2011</p>The dictionary can be found online on the <a href='https://cpd.uni-koeln.de'>Cologne University</a> website</p><p>Encoded by Bodhirasa 2024.</p>",
        website = "https://cpd.uni-koeln.de",
        source_lang = "pi",
        target_lang = "en"
    )

    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = pth.cpd_gd_path,
        md_path = pth.cpd_mdict_path,
        dict_name= "cpd",
        icon_path = None,
        zip_up=True,
        delete_original=True
    )
    
    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_vars,
        dict_data
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