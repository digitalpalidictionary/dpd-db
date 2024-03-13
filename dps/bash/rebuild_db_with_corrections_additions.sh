#!/usr/bin/env bash

# build dpd.db from scratch using backup_tsv with additions and corrections and making goldendict 

set -e

git fetch

git checkout origin/main -- db/backup_tsv/dpd_headwords.tsv

# git checkout origin/main -- db/backup_tsv/dpd_roots.tsv

dps/scripts/backup_all_dps.py

# Define filenames
FILENAMES=("sbs.tsv" "russian.tsv" "dpd_roots.tsv")

# Copy files from dps/backup/ to backup_tsv/
for file in "${FILENAMES[@]}"; do
    cp -rf ./dps/backup/$file ./backup_tsv/$file
done

# dps/scripts/move_new_words.py

scripts/bash/build_db.sh

dps/scripts/add_combined_view.py

python -c "from gui.corrections_check_feedback import apply_all_suggestions; apply_all_suggestions()"

# exporter/goldendict/export_gd_mdict.py

git checkout -- pyproject.toml

git checkout -- db/backup_tsv/dpd_headwords.tsv


