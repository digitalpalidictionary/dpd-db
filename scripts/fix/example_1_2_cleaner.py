#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.dpd_fields_functions import clean_example
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sandhi_contraction import SandhiContractionFinder


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    sandhi_dict = SandhiContractionFinder().get_sandhi_contractions_simple()

    for counter, i in enumerate(db):
        if i.meaning_1 == "":
            if i.example_1:
                i.example_1 = clean_example(i.example_1, sandhi_dict)
                print()
                print(i.lemma_1)
                print(i.example_1)

            if i.example_2:
                i.example_2 = clean_example(i.example_2, sandhi_dict)
                print()
                print(i.lemma_1)
                print(i.example_2)

    db_session.commit()


if __name__ == "__main__":
    main()
