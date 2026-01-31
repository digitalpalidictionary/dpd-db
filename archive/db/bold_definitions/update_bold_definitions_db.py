#!/usr/bin/env python3

"""Update the bold definitions table from a previously saved tsv."""

from rich import print
from db.db_helpers import get_db_session
from db.models import BoldDefinition
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict


def main():
    pr.tic()
    pr.title("adding bold definitions to db")
    pth = ProjectPaths()

    pr.green("reading tsv")
    bold_definitions = read_tsv_dot_dict(pth.bold_definitions_tsv_path)
    print("ok")

    pr.green_title("processing tsv")
    db_session = get_db_session(pth.dpd_db_path)
    add_to_db = []
    for count, i in enumerate(bold_definitions):
        bd = BoldDefinition()
        bd.update_bold_definition(
            i.file_name,
            i.ref_code,
            i.nikaya,
            i.book,
            i.title,
            i.subhead,
            i.bold,
            i.bold_end,
            i.commentary,
        )

        add_to_db.append(bd)

        if count % 50000 == 0:
            pr.counter(count, len(bold_definitions), i.bold)

    pr.green("adding to db")
    db_session.execute(BoldDefinition.__table__.delete())  # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    pr.yes("ok")
    pr.toc()


if __name__ == "__main__":
    main()
