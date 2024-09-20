#!/usr/bin/env python3

"""Fix spaces around bold tags in compound construction."""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    count = 0
    for counter, i in enumerate(db):
        # if re.findall(r".*? </b>", i.compound_construction):
        if "<b> " in i.compound_construction:
            # i.compound_construction = i.compound_construction.replace(
                # " +</b>", "</b> +")
            print(i.lemma_1)
            print(i.compound_construction)
            pyperclip.copy(i.lemma_1)
            count += 1
            input()
    
    print(count)
    # db_session.commit()


if __name__ == "__main__":
    main()
