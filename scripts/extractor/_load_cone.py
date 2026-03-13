import json
from tools.printer import printer as pr
from scripts.extractor._read_cone import extract_cone_headwords


def load_cone_dictionary(cone_path):
    pr.green_tmr("loading cone")
    with open(cone_path, "r", encoding="utf-8") as f:
        cone_dict = json.load(f)
    pr.yes(f"{len(cone_dict)}")
    return cone_dict


def get_cone_headwords(cone_dict):
    pr.green_tmr("extracting cone headwords")
    cone_headwords = extract_cone_headwords(cone_dict)
    pr.yes(f"{len(cone_headwords)}")
    return cone_headwords
