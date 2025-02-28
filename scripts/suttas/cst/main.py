from pathlib import Path
from scripts.suttas.cst.an import extract_an_data
from scripts.suttas.cst.dn import extract_dn_data
from scripts.suttas.cst.kn10 import extract_kn10_data
from scripts.suttas.cst.kn12 import extract_kn12_data
from scripts.suttas.cst.kn13 import extract_kn13_data
from scripts.suttas.cst.kn14 import extract_kn14_data
from scripts.suttas.cst.kn15 import extract_kn15_data
from scripts.suttas.cst.kn16 import extract_kn16_data
from scripts.suttas.cst.kn17 import extract_kn17_data
from scripts.suttas.cst.kn3 import extract_kn3_data
from scripts.suttas.cst.kn4 import extract_kn4_data
from scripts.suttas.cst.kn5 import extract_kn5_data
from scripts.suttas.cst.kn6 import extract_kn6_data
from scripts.suttas.cst.kn9 import extract_kn9_data
from scripts.suttas.cst.mn import extract_mn_data
from scripts.suttas.cst.modules import make_soup, write_cst_tsv
from scripts.suttas.cst.sn import extract_sn_data
from scripts.suttas.cst.kn1 import extract_kn1_data
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths

pth = ProjectPaths()

PROCESSING_STEPS = [
    (["dn1", "dn2", "dn3"], extract_dn_data),
    (["mn1", "mn2", "mn3"], extract_mn_data),
    (["sn1", "sn2", "sn3", "sn4", "sn5"], extract_sn_data),
    (
        ["an2", "an3", "an4", "an5", "an6", "an7", "an8", "an9", "an10", "an11"],
        extract_an_data,
    ),
    (["kn1"], extract_kn1_data),
    (["kn3"], extract_kn3_data),
    (["kn4"], extract_kn4_data),
    (["kn5"], extract_kn5_data),
    (["kn6"], extract_kn6_data),
    (["kn7"], extract_kn5_data),
    (["kn8"], extract_kn6_data),
    (["kn9"], extract_kn9_data),
    (["kn10", "kn11"], extract_kn10_data),
    (["kn12"], extract_kn12_data),
    (["kn13"], extract_kn13_data),
    (["kn14"], extract_kn14_data),
    (["kn15"], extract_kn15_data),
    (["kn16"], extract_kn16_data),
    (["kn17"], extract_kn17_data),
]


def extract_sutta_data(cst_data, book_list, extract_x_data):
    source_path = Path("/home/bodhirasa/Code/dpd-db/resources/dpd_submodules/cst")

    for file_string in book_list:
        file_list = cst_texts[file_string]

        for file_path in file_list:
            file_path = Path(file_path)
            file_path = pth.cst_xml_dir / file_path.with_suffix(".xml")

            relative_path = file_path.relative_to(source_path)

            soup = make_soup(file_path)
            extracted_data = extract_x_data(soup, relative_path)
            if extracted_data:
                cst_data.extend(extracted_data)

    return cst_data


def main():
    cst_data = []

    for book_list, extract_function in PROCESSING_STEPS:
        cst_data = extract_sutta_data(cst_data, book_list, extract_function)

    output_tsv = "scripts/suttas/cst/cst.tsv"
    write_cst_tsv(output_tsv, cst_data)


if __name__ == "__main__":
    main()
