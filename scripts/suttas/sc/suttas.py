
import re

from scripts.suttas.sc.modules import update_data_dict
from tools.paths import ProjectPaths

pth = ProjectPaths()


def extract_pali(file_path, pali_data, eng_data):
    """Extract the pali data from the json file using logic."""

    data_dict = {}
    folder_name = file_path.parent.name
    folder_name_clean = re.sub(r"\d", "", folder_name)
    folder_parent = file_path.parent.parent.name

    code = None
    book = None
    vagga = None
    sutta = None
    eng_sutta = ""

    for line_code, pali_text in pali_data.items():
        eng_text = eng_data.get(line_code, "")
        
        if folder_name_clean in ["dn", "mn", "kp"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name_clean in ["sn"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
            if ":0.3" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name_clean in ["an"] and folder_name not in ["an1", "an2"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
            if ":0.3" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name_clean in ["an"] and folder_name in ["an2"]:
            if ":0.1" in line_code:
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
            if ":1.0" in line_code:
                code = line_code.replace(":1.0", "")
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

                # check if sutta only contains numbers and -
                if not bool(re.match("[0-9-]", sutta)):
                    update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name_clean in ["vagga"] and folder_parent in ["ud"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name_clean in ["vagga"] and folder_parent in ["iti"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                nipata = pali_text.strip()
            if ":0.3" in line_code:
                vagga = pali_text.strip()
            if ":0.4" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

                vagga = f"{nipata} {vagga}"

                update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name_clean in ["vagga"] and folder_parent in ["snp"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

                update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name_clean in ["vv", "thag", "cp", "ja"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                nipata = pali_text.strip()
            if ":0.3" in line_code:
                vagga = pali_text.strip()
            if ":0.4" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

                vagga = f"{nipata}, {vagga}"

                update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name in ["pv", "thig", "mnd"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
            if ":0.3" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name in ["tha-ap", "thi-ap"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
            if ":0.3" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name in ["bv"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

                update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name in ["cnd"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
                sutta = pali_text.strip()  # for cnd23:0.2 Khaggavisāṇasuttaniddesa
            if ":0.3" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            # must be a digit
            if ":0.4" in line_code and re.findall(r"\d", pali_text.strip()):
                vagga = f"{vagga}, {sutta}"
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name in ["ps"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
            if ":0.3" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

                update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

        if folder_name in ["mil"]:
            if ":0.1" in line_code:
                code = line_code.replace(":0.1", "")
                book = pali_text.strip()
            if ":0.2" in line_code:
                vagga = pali_text.strip()
                sutta = pali_text.strip()
            if ":0.3" in line_code:
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            # must be a digit
            if ":0.4" in line_code and re.findall(r"\d", pali_text.strip()):
                vagga = f"{vagga}, {sutta}"
                sutta = pali_text.strip()
                eng_sutta = eng_text.strip()

            update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict)

    return data_dict

