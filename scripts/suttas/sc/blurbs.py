from pathlib import Path
import re

from scripts.suttas.sc.modules import open_sc_json


def add_blurbs_to_sc_data(blurb_data, sc_data):
    """Add blurbs to the sc_data dictionary."""

    for blurb_code, blurb in blurb_data.items():
        clean_code = re.sub(r".+:", "", blurb_code)
        if clean_code in sc_data:
            sc_data[clean_code]["blurb"] = blurb

    return sc_data


def process_blurbs(sc_data):
    """Add the blurbs to the sc_data dictionary"""

    root_dir = Path("resources/sc-data/sc_bilara_data/root/en/blurb")
    for file_path in root_dir.iterdir():
        if file_path.is_file():
            blurb_data = open_sc_json(file_path)
            add_blurbs_to_sc_data(blurb_data, sc_data)
    
    return sc_data



if __name__ == "__main__":
    pass
    # json_file = 'resources/sc-data/additional-info/blurbs.json'
    # tsv_file = 'scripts/suttas/sc/sc_blurb.tsv'
    # blurbs = extract_blurbs(json_file)