#!/usr/bin/env python3
# coding: utf-8


from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.printer import p_title, p_green, p_yes

class GlobalVars():
    pth = ProjectPaths()
    dict_data: list[DictEntry] = []

def convert_tab_to_dict(g: GlobalVars):
    """Open .tab files and make python dict."""

    p_green("english - sinhala")

    # english_sinhala
    with open(g.pth.eng_sin_source_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            line = line.replace("\t\t", "\t")
            try:
                key, value = line.split("\t", 1)
            except ValueError:
                pass
            
            dict_entry = DictEntry(
                word = key,
                definition_html = value,
                definition_plain = "",
                synonyms = []
            )
            g.dict_data.append(dict_entry)
    
    len_eng_sin = len(g.dict_data)
    p_yes(len_eng_sin)

    p_green("sinhala - english")

    # sinhala_english
    with open(g.pth.sin_eng_source_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            line = line.replace("\t\t", "\t")
            try:
                key, value = line.split("\t", 1)
            except ValueError:
                pass

            dict_entry = DictEntry(
                word = key,
                definition_html = value,
                definition_plain = "",
                synonyms = []
            )
            g.dict_data.append(dict_entry)

    p_yes(len(g.dict_data)-len_eng_sin)


def export_goldendict_and_mdict(g: GlobalVars):
    
    dict_info = DictInfo(
        bookname = "Sinhala-English English-Sinhala",
        author = "University of Colombo School of Computing",
        description = """Sinhala-English / English-Sinhala Dictionary""",
        website = "https://ucsc.cmb.ac.lk/ltrl/projects/EnSiTip/",
        source_lang = "si",
        target_lang = "en",
    )
    
    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = g.pth.sin_eng_sin_gd_path,
        md_path = g.pth.sin_eng_sin_mdict_path,
        dict_name= "si-en-si",
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
    p_title("exporting sinhala-english-sinhala to GoldenDict and MDict")
    g = GlobalVars()
    convert_tab_to_dict(g)
    export_goldendict_and_mdict(g)
    toc()


if __name__ == "__main__":
    main()