#!/usr/bin/env bash

# build dpd.db from scratch using backup_tsv with additions and corrections and making goldendict 

git pull

set -e
test -e dpd.db || touch dpd.db

dps/scripts/move_new_words.py

bash/build_db.sh

dps/scripts/add_combined_view.py

python -c "from gui.corrections_check_feedback import apply_all_suggestions; apply_all_suggestions()"

exporter/exporter.py

git checkout -- pyproject.toml

git checkout -- backup_tsv/dpd_headwords.tsv


