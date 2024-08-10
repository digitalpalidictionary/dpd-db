#!/usr/bin/env python3

"""Update the bold definitions table from a previously saved tsv."""

from rich import print
from db.db_helpers import get_db_session
from db.models import BoldDefinition
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv_dot_dict


def main():
    tic()
    print("[bright_yellow]adding bold definitions to db")
    pth = ProjectPaths()

    print("[green]reading tsv", end=" ")
    bold_definitions = read_tsv_dot_dict(pth.bold_definitions_tsv_path)
    print("ok")

    print("[green]processing tsv")
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
            i.commentary)
        
        add_to_db.append(bd)

        if count % 50000 == 0:
            print(f"{count:>8} / {len(bold_definitions):<8}{i.bold}")
    
    print("[green]adding to db", end=" ")
    db_session.execute(BoldDefinition.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("ok")
    toc()


if __name__ == "__main__":
    main()
