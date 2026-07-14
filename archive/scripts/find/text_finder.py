"""Scratchpad to find text in CST books: edit the book list and the
filter condition, then run to print matching words."""

from rich import print

from tools.cst_sc_text_sets import make_cst_text_set
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.yellow_title("finding text in books")
    pth = ProjectPaths()
    cst_test_set = make_cst_text_set(pth, ["kn6", "kn7", "kn8", "kn9"])
    for word in cst_test_set:
        if word.startswith("ati"):
            print(f"[cyan]{word}")


if __name__ == "__main__":
    main()
