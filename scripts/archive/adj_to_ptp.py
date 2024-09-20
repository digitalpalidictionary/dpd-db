#!/usr/bin/env python3

"""Convert part of speech - adj to ptp."""

import re
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()

    for i in dpd_db:
        if (
            i.derivative == "kicca" and
            i.pos == "adj"
        ):
            i.pos = "ptp"
            i.pattern = "a ptp"
            i.grammar = re.sub("adj, ptp of", "ptp of", i.grammar)
            i.grammar = re.sub("adj, from", "ptp of", i.grammar)
            if "adj, in comps" in i.grammar:
                i.grammar = re.sub("adj, in comps, ", "", i.grammar)
                i.grammar += ", in comps"

            if "adj" in i.grammar:
                i.grammar = re.sub("adj", "ptp", i.grammar)

            print(f"{i.id:<10}{i.lemma_1:<20}{i.grammar:<30}{i.pattern:<10}")

    db_session.commit


if __name__ == "__main__":
    main()
