#!/usr/bin/env bash

# update data in dpd.db from from backup_tsv with additions and corrections

git pull

set -e

dps/scripts/move_new_words.py

scripts/db_update_from_tsv.py

python -c "from gui.corrections_check_feedback import apply_all_suggestions; apply_all_suggestions()"

mkdpd.sh

git checkout -- pyproject.toml

git checkout -- backup_tsv/dpd_headwords.tsv
