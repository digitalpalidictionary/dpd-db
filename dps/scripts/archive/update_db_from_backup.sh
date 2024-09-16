#!/usr/bin/env bash

# update data in dpd.db from from dps backup_tsv

git fetch

git checkout origin/main -- db/backup_tsv/dpd_headwords.tsv

git checkout origin/main -- db/backup_tsv/dpd_roots.tsv

set -e

dps/scripts/backup_all_dps.py

# Define filenames
FILENAMES=("sbs.tsv" "russian.tsv" "dpd_roots.tsv" "dpd_headwords.tsv" "ru_roots")

# Copy files from db/backup_tsv/ to temp/
for file in "${FILENAMES[@]}"; do
    cp -rf ./db/backup_tsv/$file ./temp/$file
done

# Copy files from dps/backup/ to db/backup_tsv/
for file in "${FILENAMES[@]}"; do
    cp -rf ./dps/backup/$file ./db/backup_tsv/$file
done

scripts/db_update_from_tsv.py

# Move files back from temp/ to db/backup_tsv/ after all other scripts have completed
for file in "${FILENAMES[@]}"; do
    mv -f ./temp/$file ./db/backup_tsv/$file
done



