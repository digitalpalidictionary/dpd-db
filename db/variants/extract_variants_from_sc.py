"""Extract variants readings from CST texts."""

import json
from pathlib import Path
from icecream import ic

from db.variants.variant_types import VariantsDict
from db.variants.extract_variants_from_cst import key_cleaner

from tools.paths import ProjectPaths
from tools.printer import p_green_title, p_counter


def get_sc_file_list(pth: ProjectPaths) -> list[Path]:
    """Get a list of all SC variants files."""

    root_dir = pth.sc_variants_dir
    file_list = sorted([file for file in root_dir.rglob("*") if file.is_file()])

    return file_list


def get_json_data(file_path: Path) -> dict[str, str]:
    """Get the JSON data from the file_path"""

    with open(file_path, "r", encoding="UTF-8") as f:
        return json.load(f)


def extract_variants(
        json_data: dict[str, str],
        variants_dict: VariantsDict
) -> VariantsDict:
    """"Extract variants from a SC json file."""

    for reference_code, data in json_data.items():
        
        # data is a list of items separated by '|'
        data_list = data.split("|")
        
        for d in data_list:
            d = d.strip()
            d = d.replace("ṁ", "ṃ")
            
            # root_word / variants pairs are separated by '→'
            variants_list = [part.strip() for part in d.split("→", maxsplit=1)] 
            
            # normal case
            if len(variants_list) == 2:
                root_word, variants = variants_list

            # fallback case where there is no '→'
            else:
                variants = variants_list[0]
            
            # sometimes there are multiple variants separated by ';'
            for variant in variants.split(";"):

                # ensure outer dictionary entry exists
                if root_word not in variants_dict:
                    variants_dict[root_word] = {}

                # ensure sc entry exists
                if "sc" not in variants_dict[root_word]:
                    variants_dict[root_word]["sc"] = {}

                # ensure inner dictionary entry exists
                if reference_code not in variants_dict[root_word]["sc"]:
                    variants_dict[root_word]["sc"][reference_code] = []
    
                variants_dict[root_word]["sc"][reference_code].append(variant)
                # ic(reference_code, root_word, variant)

    return variants_dict


def extract_variants_from_sc(
        variants_dict: VariantsDict, pth: ProjectPaths) -> VariantsDict:
    """This is the main function."""
    
    p_green_title("extracting variants from SC texts")
    
    
    file_list: list[Path] = get_sc_file_list(pth)
    
    for counter, file_name in enumerate(file_list):
        
        if counter % 500 == 0:
            p_counter(counter, len(file_list), file_name.name)
        
        json_data = get_json_data(file_name)
        variants_dict = extract_variants(json_data, variants_dict)

    return variants_dict