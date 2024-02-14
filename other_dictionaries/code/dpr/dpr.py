"""Export DPR Analysis data into Goldendict, MDict and JSON formats."""

import json
import re

from rich import print

from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]exporing dpr analysis data into various formats")

    pth = ProjectPaths()

    print("[green]processing data")
    
    with open(pth.dpr_source_path) as file:
        dpr_data = json.load(file)

    with open(pth.dpr_css_path) as file:
        dpr_css = file.read()

    dpr_data_list = []

    for counter, (headword, breakup) in enumerate(dpr_data.items()):
        dpr_part1 = re.sub("(.+) \\(.+", "\\1", breakup)
        dpr_part2 = re.sub("(.+ )(\\(.+$)", "\\2", breakup)

        html = dpr_css
        html += "<div class='dpr'>"
        html += "<p class='dpr'>"
        html += dpr_part1
        html += f"<span class='bracket'> {dpr_part2}</span>"
        html += "</p></div>"
        
        if "ṃ" in headword:
            synonyms = add_niggahitas([headword])
        else:
            synonyms = []

        dpr_data_list.append({
            "word": headword, 
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms            
            })
        
        if counter % 100000 == 0:
            print(f"{counter:>10} / {len(dpr_data):<10}{headword}")

    # sort into pali alphabetical order
    print("[green]sorting data")
    dpr_data_list = sorted(dpr_data_list, key=lambda x: pali_sort_key(x["word"]))

    # save as json
    print("[green]saving json")
    with open(pth.dpr_json_path, "w") as file:
        json.dump(dpr_data_list, file, indent=4, ensure_ascii=False)

    # save as goldendict
    print("[green]saving goldendict")

    # TODO find out more details, website etc

    bookname = "DPR Analysis"
    author = "Ven. Yuttadhammo"
    description = "<h3>DPR Analysis</h3><p>DPR Analysis was the first known attempt to digitally anaylse and deconstruct Pāḷi compounds. The code was written in JavaScript by Ven. Yuttadhammmo.</p><p>The JSON file used to create this dictionary is from the Tipitaka Pali Projector repository on GitHub. It seems to be an attempt to run each word in the CST through DPR Analysis and produce a flat lookup file, rather than using DPR's dynamic process. The results are slightly different to the actual DPR Analysis which produces multiple solutions. Still, it is useful as a reference.</p><p><a href='https://www.digitalpalireader.online/'>Digital Pali Reader Online</a></p><p>Encoded by Bodhirasa 2024.</p>"
    website = "https://www.digitalpalireader.online/"

    ifo = ifo_from_opts({
            "bookname": bookname,
            "author": author,
            "description": description,
            "website": website
            })

    export_words_as_stardict_zip(dpr_data_list, ifo, pth.dpr_gd_path)

    # save as mdict
    print("[green]saving mdict")
    output_path = str(pth.dpr_mdict_path)

    export_to_mdict(
        dpr_data_list,
        output_path,
        bookname,
        description)

    toc()


if __name__ == "__main__":
    main()

