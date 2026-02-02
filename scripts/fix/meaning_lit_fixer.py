#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_1 == "")
        .filter(DpdHeadword.meaning_lit == "")
        .filter(DpdHeadword.meaning_2.ilike("%lit.%"))
        .all()
    )

    error_list = []
    for counter, i in enumerate(db):
        try:
            meaning, lit = i.meaning_2.split("; lit.", 1)
        except ValueError:
            error_list.append(i.lemma_1)
        pr.info(i.lemma_1)
        pr.info(i.meaning_2)
        pr.info(f"meaning: {lit}")
        pr.info("")

        i.meaning_2 = meaning
        i.meaning_lit = lit

    db_session.commit()

    pr.error(f"{error_list}")


if __name__ == "__main__":
    main()
