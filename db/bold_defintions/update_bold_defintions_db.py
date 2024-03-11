#!/usr/bin/env python3

"""Update the bold definitions table from a previously saved tsv."""

from rich import print
from db.get_db_session import get_db_session
from db.models import BoldDefintion
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv_dot_dict


def main():
    tic()
    print("[bright_yellow]adding bold defintions to db")
    pth = ProjectPaths()

    print("[green]reading tsv", end=" ")
    bold_defintions = read_tsv_dot_dict(pth.bold_defintions_tsv_path)
    print("ok")

    print("[green]processing tsv")
    db_session = get_db_session(pth.dpd_db_path)
    add_to_db = []
    for count, i in enumerate(bold_defintions):
        bd = BoldDefintion()
        bd.update_bold_defintion(
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
            print(f"{count:>8} / {len(bold_defintions):<8}{i.bold}")
    
    print("[green]adding to db", end=" ")
    db_session.execute(BoldDefintion.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("ok")
    toc()


if __name__ == "__main__":
    main()
