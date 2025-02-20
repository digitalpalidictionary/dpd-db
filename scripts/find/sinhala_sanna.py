from pathlib import Path
import json
import re
from icecream import ic

from tools.printer import p_green, p_title
from tools.zip_up import zip_up_directory
from tools.paths import ProjectPaths

def extract_data_from_json(file_path):
    with file_path.open("r", encoding="utf-8") as file:
        extracted_data = []
        data = json.load(file)
        extracted_data.append(data.get("filename", ""))
        
        for page in data.get("pages", []):
            extracted_data.append("")
            extracted_data.append(str(page.get("pageNum", "")))
            for entry in page.get("pali", {}).get("entries", []):
                text = entry.get("text", "")
                if text and re.fullmatch(r"[0-9. ]*", text):
                    extracted_data.append(text)
                else:
                    text_split = text.split()
                    extracted_data.extend(text_split)
        return extracted_data

def main():
    p_title("extracting sinhala words for sanna ")
    pth = ProjectPaths()
    input_directory = Path(pth.bjt_sinhala_dir)
    output_dir = Path(pth.bjt_dir / "sanna/")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    p_green("extracting data from files")
    for file_path in input_directory.rglob("*.json"):
        
        extracted_data = extract_data_from_json(file_path)
        output_file = output_dir / f"{file_path.stem}.tsv"
        with output_file.open("w", encoding="utf-8") as tsv_file:
            tsv_file.write('\n'.join(extracted_data))

    p_green("zipping up")
    zip_up_directory(
        output_dir,
        delete_original=True
    )

if __name__ == "__main__":
    main()
