#!/usr/bin/env python3.11

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot, Russian, SBS
from scripts.db_rebuild_from_tsv import make_pali_word_table_data
from scripts.db_rebuild_from_tsv import make_pali_root_table_data
from scripts.db_rebuild_from_tsv import make_russian_table_data
from scripts.db_rebuild_from_tsv import make_sbs_table_data
from tools.paths import ProjectPaths as PTH
from tools.tic_toc import tic, toc


def main():
    print("[bright_yellow]updating db from tsvs")
    tic()
    db_session = get_db_session(PTH.dpd_db_path)

    db_session.execute(PaliWord.__table__.delete())
    db_session.execute(PaliRoot.__table__.delete())
    db_session.execute(Russian.__table__.delete())
    db_session.execute(SBS.__table__.delete())

    make_pali_word_table_data(db_session)
    make_pali_root_table_data(db_session)
    make_russian_table_data(db_session)
    make_sbs_table_data(db_session)

    db_session.commit()
    db_session.close()

    print("[bright_green]database restored successfully")
    toc()


if __name__ == "__main__":
    main()
