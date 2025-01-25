"""Extract variants readings from CST texts."""


import json
from pathlib import Path
from bs4 import BeautifulSoup

from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.pali_alphabet import pali_alphabet
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_title, p_yes
from tools.tic_toc import bip, bop, tic, toc

pth = ProjectPaths()


def get_cst_file_list():
    """Get a list of CST files."""

    cst_xml_roman_dir = pth.cst_xml_roman_dir
    files = [f for f in cst_xml_roman_dir.iterdir() if f.is_file()]
    return files


def make_soup(file):
    """Make a soup from a CST file."""

    with open(file, "r", encoding="UTF-16") as f:
        file_contents = f.read()
        soup = BeautifulSoup(file_contents, "xml")
        return soup


def key_cleaner(key):
    """Remove non-Pāḷi characters from the key"""
    
    key_clean = ''.join(c for c in key.lower() if c in pali_alphabet)
    key_clean = key_clean.lower()
    return key_clean


def extract_variants(soup, variants_dict, book_name):
    """Extract variants from a CST file."""

    notes = soup.find_all('note')
    for note in notes:
        # Get preceding text node
        preceding_text = note.previous_sibling
        
        if preceding_text:
            if text_str := preceding_text.text.strip():
                # Split text into words and get last word before note
                words = text_str.split()
                if words:
                    key = words[-1]
                    key_clean = key_cleaner(key)
                    value = note.get_text(strip=True).lower()
                    
                    # Ensure outer dictionary entry exists
                    if key_clean not in variants_dict:
                        variants_dict[key_clean] = {}

                    # Ensure inner dictionary entry exists
                    if book_name not in variants_dict[key_clean]:
                        variants_dict[key_clean][book_name] = []

                    variants_dict[key_clean][book_name].append(value)

    return variants_dict


def get_book_name(xml_filename: Path) -> str:
    """Convert filename.xml into a book code."""

    txt_filename = str(xml_filename.with_suffix(".txt").name)
    
    # Search through the dictionary
    for key, txt_files in cst_texts.items():
        if any(file == txt_filename for file in txt_files):
            return key
    raise ValueError(f"No matching key found for XML file: {xml_filename}")


def save_json(variants_dict):
    """Save variants to json"""

    with open("temp/variants.json", "w") as f:
        json.dump(variants_dict, f, ensure_ascii=False, indent=2)


def export_to_goldendict(variants_dict):
    """Convert dict to HTML and export to GoldenDict, MDict"""

    dict_data: list[DictEntry] = []
    for key, data in variants_dict.items():
        html_list = ["<table>"]
        for book, variant_list in data.items():
            for item in variant_list:
                html_list.append(f"<tr><th>{book}</th><td>{item}</td></tr>")
        html_list.append("</table>")
        html = "\n".join(html_list)

        dict_entry = DictEntry(
            word=key,
            definition_html=html,
            definition_plain="",  # Consider populating this too
            synonyms=[]
        )
        dict_data.append(dict_entry)

    dict_info = DictInfo(
        bookname = "DPD Variant Readings",
        author = "Bodhirasa",
        description = "Variant readings as found in CST texts.",
        website = "wwww.dpdict.net",
        source_lang = "pi",
        target_lang = "pi"
    )

    dict_vars = DictVariables(
        css_path = None,
        js_paths = None,
        gd_path = pth.share_dir,
        md_path = pth.share_dir,
        dict_name= "dpd-variants",
        icon_path = None,
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


def main():

    tic()
    p_title("variants dict")

    variants_dict: dict[str, dict[str, list[str]]] = {} 

    p_green_title("extracting variants from CST texts")
    files = get_cst_file_list()

    bip()
    for counter, file_name in enumerate(files):
        soup = make_soup(file_name)
        book_name = get_book_name(file_name)
        variants_dict = extract_variants(soup, variants_dict, book_name)
        if counter % 25 == 0:
            p_counter(counter, len(files), file_name.name)
            bip()
    
    p_green("variants extracted")
    p_yes(len(variants_dict))

    save_json(variants_dict)
    export_to_goldendict(variants_dict)

    toc()

if __name__ == "__main__":
    main()