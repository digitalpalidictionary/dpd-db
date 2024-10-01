#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import p_red


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for counter, i in enumerate(db):
        if i.lemma_clean not in i.inflections_list:
            p_red(f"{i.id}\t{i.lemma_1}")


if __name__ == "__main__":
    main()
