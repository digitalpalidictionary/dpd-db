#!/usr/bin/env bash

# build dpd.db from scratch using dps backup_tsv and making goldendict

git fetch

git checkout origin/main -- db/backup_tsv/dpd_headwords.tsv

git checkout origin/main -- db/backup_tsv/dpd_roots.tsv

set -e
test -e dpd.db || touch dpd.db

# Directory where backups are stored
BACKUP_DIR="dps/backup/"

# Get today's date
TODAY=$(date "+%Y-%m-%d")

# Check the modification date of a file (for example, dpd_headwords.tsv)
FILE_DATE=$(stat -c %y "${BACKUP_DIR}dpd_headwords.tsv" | cut -d' ' -f1)

# Check if backups for today exist in db/backup_tsv/
if [[ "$FILE_DATE" == "$TODAY" ]]; then
    echo "Backups for today already exist."
else
    dps/scripts/backup_all_dps.py
fi

# Define filenames
FILENAMES=("sbs.tsv" "russian.tsv" "dpd_roots.tsv" "dpd_headwords.tsv")

# Copy files from db/backup_tsv/ to temp/
for file in "${FILENAMES[@]}"; do
    cp -rf ./db/backup_tsv/$file ./temp/$file
done

# Copy files from dps/backup/ to db/backup_tsv/
for file in "${FILENAMES[@]}"; do
    cp -rf ./dps/backup/$file ./db/backup_tsv/$file
done

scripts/bash/build_db.sh

dps/scripts/add_combined_view.py

# Move files back from temp/ to db/backup_tsv/ after all other scripts have completed
for file in "${FILENAMES[@]}"; do
    mv -f ./temp/$file ./db/backup_tsv/$file
done

exporter/goldendict/export_gd_mdict.py

git checkout -- pyproject.toml



