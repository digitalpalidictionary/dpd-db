"""Export DPR Analysis data into Goldendict, MDict and JSON formats."""

import json
import re

from rich import print

from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]exporting DPR Analysis data to GoldenDict and MDict")

    pth = ProjectPaths()

    print("[green]processing data")
    
    with open(pth.dpr_source_path) as file:
        dpr_data = json.load(file)

    with open(pth.dpr_css_path) as file:
        dpr_css = file.read()

    dict_data: list[DictEntry] = []

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

        dict_entry = DictEntry(
            word = headword,
            definition_html = html,
            definition_plain = "",
            synonyms = synonyms)
        dict_data.append(dict_entry)
        
        if counter % 100000 == 0:
            print(f"{counter:>10} / {len(dpr_data):<10}{headword}")

    # save as goldendict
    print("[green]saving goldendict")

    # TODO find out more details, website etc

    dict_info = DictInfo(
        bookname = "DPR Analysis",
        author = "Ven. Yuttadhammo",
        description = """<h3>DPR Analysis</h3><p>DPR Analysis was the first known attempt to digitally anaylse and deconstruct Pāḷi compounds. The code was written in JavaScript by Ven. Yuttadhammmo.</p><p>The JSON file used to create this dictionary is from the Tipitaka Pali Projector repository on GitHub. It seems to be an attempt to run each word in the CST through DPR Analysis and produce a flat lookup file, rather than using DPR's dynamic process. The results are slightly different to the actual DPR Analysis which produces multiple solutions. Still, it is useful as a reference.</p><p><a href='https://www.digitalpalireader.online/'>Digital Pali Reader Online</a></p><p>Encoded by Bodhirasa 2024.</p>""",
        website = "https://www.digitalpalireader.online/",
        source_lang = "pi",
        target_lang = "pi"
    )

    dict_vars = DictVariables(
        css_path = pth.dpr_css_path,
        js_paths = None,
        gd_path = pth.dpr_gd_path,
        md_path = pth.dpr_mdict_path,
        dict_name= "dpr",
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

