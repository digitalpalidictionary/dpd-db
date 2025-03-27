#!/usr/bin/env python3

"""Find CST Abbreviations in the db and write them to a tsv file."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tsv_read_write import write_tsv_list


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).filter(DpdHeadword.pos == "abbrev").all()
    db = sorted(db, key=lambda x: x.lemma_2)

    header = ["abbreviation", "meaning"]
    data = []
    file_path = "shared_data/abbreviations/abbreviations_cst.tsv"
    for counter, i in enumerate(db):
        data.append((i.lemma_2, i.meaning_1))

    write_tsv_list(file_path, header, data)


if __name__ == "__main__":
    main()
