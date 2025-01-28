""""Saving and Exporting modules."""

import json
import re

from db.variants.variants_modules import VariantsDict

from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths


def save_json(variants_dict: VariantsDict) -> None:
    """Save variants to json"""

    with open("temp/variants.json", "w") as f:
        json.dump(variants_dict, f, ensure_ascii=False, indent=2)


def make_synonyms(synonyms_list: list[str], variant: str) -> list[str]:
    """Make synonyms for a word."""

    # find single words
    variant_clean = re.sub(r" \(.+", "", variant)
    words = variant_clean.split()
    if len(words) == 1:
        if variant_clean not in synonyms_list:
            synonyms_list.append(variant_clean)
    
    return synonyms_list


def make_synonyms_bjt(synonyms_list: list[str], variant: str) -> list[str]:
    """Make synonyms for a word in BJT text."""

    # BJT variants are in the format: "rūpādivaggo paṭhamo – machasaṃ, PTS"
    variant_clean = re.sub(r" – .+", "", variant)
    words = variant_clean.split()
    if len(words) == 1:
        if variant_clean not in synonyms_list:
            synonyms_list.append(variant_clean)
    
    return synonyms_list


def export_to_goldendict_mdict(
        variants_dict: VariantsDict, pth: ProjectPaths) -> None:
    """Convert dict to HTML and export to GoldenDict, MDict"""

    dict_data: list[DictEntry] = []
    
    for word, data in variants_dict.items():
        
        html_list: list[str] = ["<table>"]
        synonyms_list: list[str] = []

        # add various niggahita to synonyms 
        if "ṃ" in word or "ṁ" in word:
            synonyms_list = add_niggahitas([word])

        for corpus, data2 in data.items():
            for book, variants in data2.items():
                for variant in variants:
                    if corpus == "MST" or corpus == "CST":
                        synonyms_list = make_synonyms(synonyms_list, variant)
                    if corpus == "BJT":
                        synonyms_list = make_synonyms_bjt(synonyms_list, variant)
                    
                    # add various niggahitas to synonyms
                    synonyms_list = add_niggahitas(synonyms_list)
                    
                    html_list.append(f"<tr><th>{corpus}</th><td>{book}</td><td>{variant}</td></tr>")
        
        html_list.append("</table>")
        html: str = "\n".join(html_list)

        dict_entry = DictEntry(
            word=word,
            definition_html=html,
            definition_plain="",
            synonyms=synonyms_list
        )
        dict_data.append(dict_entry)

    dict_info = DictInfo(
        bookname="DPD Variant Readings",
        author="Bodhirasa",
        description="Variant readings as found in CST texts.",
        website="wwww.dpdict.net",
        source_lang="pi",
        target_lang="pi"
    )

    dict_vars = DictVariables(
        css_path=None,
        js_paths=None,
        gd_path=pth.share_dir,
        md_path=pth.share_dir,
        dict_name="dpd-variants",
        icon_path=None,
    )

    export_to_goldendict_with_pyglossary(
        dict_info, 
        dict_vars,
        dict_data, 
    )

    export_to_mdict(
        dict_info,
        dict_vars,
        dict_data
    )

