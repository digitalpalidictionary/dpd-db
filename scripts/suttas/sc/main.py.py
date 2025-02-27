"""
Extract sutta data from SC texts and translations.
"""
from pathlib import Path

from scripts.suttas.sc.blurbs import process_blurbs
from scripts.suttas.sc.links import process_links
from scripts.suttas.sc.modules import open_sc_json, write_sc_data_to_tsv
from scripts.suttas.sc.suttas import extract_pali

def main():
    sc_data = {}
    pali_base_dir = Path("resources/sc-data/sc_bilara_data/root/pli/ms/sutta")
    english_base_dir = Path(
        "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta"
    )
    file_list = [f for f in pali_base_dir.rglob("*") if f.is_file()]

    for pali_path in sorted(file_list):
        relative_path = pali_path.relative_to(pali_base_dir)

        pali_data = open_sc_json(pali_path)

        english_path = english_base_dir / relative_path
        english_path = Path(str(english_path).replace(
            "root-pli-ms", "translation-en-sujato"))
        if english_path.exists():
            english_data = open_sc_json(english_path)
        else:
            english_data = {}

        sc_data.update(extract_pali(pali_path, pali_data, english_data))

    sc_data = process_blurbs(sc_data)
    sc_data = process_links(sc_data)
    write_sc_data_to_tsv(sc_data)


if __name__ == "__main__":
    main()
