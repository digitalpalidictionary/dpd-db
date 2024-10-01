
from pathlib import Path
from json import loads

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.pali_text_files import cst_texts
from tools.cst_sc_text_sets import make_sc_text_set
from tools.clean_machine import clean_machine
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths


pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
cst_texts_dir = Path("resources/tipitaka-xml/romn_txt")


def main():
    books = ["abh1", "abh2", "abh3", "abh4", "abh5", "abh6", "abh7"]
    all_inflections_set = make_all_inflections_set()

    text_set = make_cst_text_set(books)
    sc_text_set = make_sc_text_set(pth, books)

    text_set = text_set | sc_text_set
    text_set = text_set - all_inflections_set
    text_set = sorted(text_set, key=pali_sort_key)

    with open("abhidhamma_unrecognised.tsv", "w") as f:
        for word in text_set:
            f.write(f"{word}\n")


def make_all_inflections_set():

    inflections_db = db_session.query(DpdHeadword.inflections).all()
    all_inflections_set = set()
    for i in inflections_db:
        all_inflections_set.update(loads(i.inflections))
    return all_inflections_set


def make_cst_text_set(books) -> set:
    text_set = set()

    for book in books:
        if book in cst_texts:
            for b in cst_texts[book]:
                filepath = cst_texts_dir.joinpath(b)
                with open(filepath) as f:
                    text_read = f.read()
                    text_clean = clean_machine(text_read)
                    text_set.update(text_clean.split())

    return text_set


if __name__ == "__main__":
    main()
