""""Saving and Exporting modules."""

import json
from db.variants.variant_types import VariantsDict

from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths


pth: ProjectPaths = ProjectPaths()

def save_json(variants_dict: VariantsDict) -> None:
    """Save variants to json"""

    with open("temp/variants.json", "w") as f:
        json.dump(variants_dict, f, ensure_ascii=False, indent=2)


def export_to_goldendict_mdict(variants_dict: VariantsDict) -> None:
    """Convert dict to HTML and export to GoldenDict, MDict"""

    dict_data: list[DictEntry] = []
    for key, data in variants_dict.items():
        html_list: list[str] = ["<table>"]
        for corpus, data2 in data.items():
            for book, variants in data2.items():
                for item in variants:
                    html_list.append(f"<tr><th>{corpus}</th><td>{book}</td><td>{item}</td></tr>")
        html_list.append("</table>")
        html: str = "\n".join(html_list)

        dict_entry = DictEntry(
            word=key,
            definition_html=html,
            definition_plain="",  # Consider populating this too
            synonyms=[]
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
        zip_up=False,
        delete_original=False
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

