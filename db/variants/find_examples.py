import json

from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    var_dict = json.loads(pth.variants_json_path.read_text(encoding="utf-8"))

    for key, value in var_dict.items():
        if "CST" in value and "MST" in value and "BJT" in value and "SYA" in value:
            print(key)


if __name__ == "__main__":
    main()
