from rich import print
from tools.cst_sc_text_sets import make_cst_text_set
from tools.paths import ProjectPaths

"""Find some text in some book."""


def main():
    pth = ProjectPaths()
    cst_test_set = make_cst_text_set(pth, ["kn6", "kn7", "kn8", "kn9"])
    for word in cst_test_set:
        # if word.endswith(("ttā", "tā", "tāya")):
        #     print(f"[yellow]{word}")
        if word.startswith("ati"):
            print(f"[cyan]{word}")


if __name__ == "__main__":
    main()
