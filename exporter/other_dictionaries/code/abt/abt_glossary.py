import csv
import re
from pathlib import Path
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.printer import p_title, p_white, p_yes
from tools.tic_toc import bip, tic, toc



def main():
    """Export Ven. Ānandajoti's Ancient BUddhist Texts Glossary to Goldendict"""

    tic()
    p_title("exporting ancient buddhist texts glossary")
    
    bip()
    p_white("processing csv")

    dict_data: list[DictEntry] = []

    source_file = "exporter/other_dictionaries/code/abt/CPED.csv"

    with open(source_file, newline="") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter='|')
        for i in csv_reader:
            word = i[0].strip()
            if ": " in i[1]:
                pos, english = re.split(":", i[1].strip(), 1)
                definition = f"{pos.rstrip('.')}. <b>{english}</b>"
            else:
                english = i[1].strip()
                definition = f"<b>{english}</b>"

            dict_entry = DictEntry(
                word = word,
                definition_html = definition,
                definition_plain = "",
                synonyms = [])
            dict_data.append(dict_entry)
    
    dict_info = DictInfo(
        bookname = "Concise Pali English Dictionary",
        author = "Ven. A. P. Buddhadatta",
        description = "Modified from the Original",
        website = "ancient-buddhist-texts.net",
        source_lang = "pi",
        target_lang = "en"
    )

    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = Path("exporter/other_dictionaries/goldendict/"),
        md_path = Path("exporter/other_dictionaries/mdict/"),
        dict_name= "cped",
        icon_path = None,
        zip_up=True,
        delete_original=True
    )

    p_yes(len(dict_data))


    export_to_goldendict_with_pyglossary(
        dict_info, 
        dict_vars,
        dict_data, 
        zip_synonyms=False,
        include_slob=True
    )

    toc()
        
if __name__ == "__main__":
    main()

