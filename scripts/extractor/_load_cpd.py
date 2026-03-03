import json
from tools.printer import printer as pr
from scripts.extractor._read_cpd import extract_cpd_headwords


def load_cpd_dictionary(cpd_path):
    pr.green("loading cpd dictionary")
    with open(cpd_path, "r", encoding="utf-8") as f:
        cpd_data = json.load(f)
    pr.yes(f"{len(cpd_data)}")
    return cpd_data


def get_cpd_headwords(cpd_data):
    pr.green("extracting cpd headwords")
    cpd_headwords = extract_cpd_headwords(cpd_data)
    pr.yes(f"{len(cpd_headwords)}")
    return cpd_headwords
