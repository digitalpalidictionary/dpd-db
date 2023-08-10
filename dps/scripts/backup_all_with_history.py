#!/usr/bin/env python3

"""Save all tables in dps/backup folder. Keep up to MAX_BACKUPS backups and then overwrite them"""


from git.repo import Repo
from rich import print
import csv
import os
import glob
import datetime

from db.get_db_session import get_db_session
from db.models import Russian, SBS, PaliWord, PaliRoot
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH
from dps.tools.paths_dps import DPSPaths as DPSPTH

MAX_BACKUPS = 10  # Set the maximum number of backups

def backup_all_tables():
    tic()
    print("[bright_yellow]Backing up all tables to dps/backup/*.tsvs")
    db_session = get_db_session(PTH.dpd_db_path)

    tables_to_backup = [
        {'class': PaliWord, 'name': "paliword", 'exclude_columns': ["created_at", "updated_at"]},
        {'class': PaliRoot, 'name': "paliroot", 'exclude_columns': ["created_at", "updated_at", "root_info", "root_matrix"]},
        {'class': SBS, 'name': "sbs", 'exclude_columns': []},
        {'class': Russian, 'name': "russian", 'exclude_columns': []}
    ]

    for table in tables_to_backup:
        backup_generic(db_session, table['class'], DPSPTH.dps_backup_dir, table['name'], table['exclude_columns'])

    db_session.close()
    # git_commit()
    toc()

def backup_generic(db_session, TableClass, backup_dir, table_name, exclude_columns=[]):
    """Generic function to backup tables to TSV."""
    print(f"[green]writing {table_name} table")
    
    # Manage old backups
    manage_backups(backup_dir, table_name)
    
    backup_filename = os.path.join(backup_dir, f"{table_name}_{get_unique_filename_suffix()}.tsv")
    db = db_session.query(TableClass).all()
    
    with open(backup_filename, 'w', newline='') as tsvfile:
        csvwriter = csv.writer(tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [column.name for column in TableClass.__mapper__.columns if column.name not in exclude_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [getattr(i, column.name) for column in TableClass.__mapper__.columns if column.name not in exclude_columns]
            csvwriter.writerow(row)

def get_unique_filename_suffix():
    """Return a unique suffix for backup filenames."""
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def manage_backups(backup_dir, table_name):
    """Delete oldest backups if they exceed the limit."""
    list_of_files = glob.glob(os.path.join(backup_dir, f"{table_name}_*.tsv"))
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    
    while len(sorted_files) >= MAX_BACKUPS:
        os.remove(sorted_files[0])
        sorted_files.pop(0)


def git_commit():
    repo = Repo("./")
    index = repo.index
    index.add(["dps/backup/*"])
    index.commit("backup all dps")


if __name__ == "__main__":
    backup_all_tables()

