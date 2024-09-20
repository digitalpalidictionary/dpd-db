#!/usr/bin/env python3

"""Save all tables to dps/backup folder."""


from rich.console import Console

import os

from db.db_helpers import get_db_session
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

from scripts.backup.backup_dpd_headwords_and_roots import backup_dpd_headwords, backup_dpd_roots
from scripts.backup.backup_ru_sbs import backup_russian, backup_sbs, backup_ru_roots

console = Console()

def backup_all_tables_dps():
    tic()
    console.print("[bold bright_yellow]Backing up all tables to dps/backup/ folder")
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    dps_headwords_path = os.path.join(dpspth.dps_backup_dir, "dpd_headwords.tsv")
    dps_roots_path = os.path.join(dpspth.dps_backup_dir, "dpd_roots.tsv")
    dps_ru_roots_path = os.path.join(dpspth.dps_backup_dir, "ru_roots.tsv")
    dps_ru_path = os.path.join(dpspth.dps_backup_dir, "russian.tsv")
    dps_sbs_path = os.path.join(dpspth.dps_backup_dir, "sbs.tsv")

    backup_dpd_headwords(db_session, pth, dps_headwords_path)
    backup_dpd_roots(db_session, pth, dps_roots_path)
    backup_russian(db_session, pth, dps_ru_path)
    backup_ru_roots(db_session, pth, dps_ru_roots_path)
    backup_sbs(db_session, pth, dps_sbs_path)

    db_session.close()
    toc()


if __name__ == "__main__":
    backup_all_tables_dps()

