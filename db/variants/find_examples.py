import json
from pathlib import Path


def main():
    variants_path = Path("temp/variants.json")
    var_dict = json.loads(variants_path.read_text())

    for key, value in var_dict.items():
        if "CST" in value and "MST" in value and "BJT" in value and "SYA" in value:
            print(key)


if __name__ == "__main__":     
    main()