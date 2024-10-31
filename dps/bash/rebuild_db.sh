#!/usr/bin/env bash

# build dpd.db from scratch or update existing one using backup_tsv with additions and corrections and making goldendict 

set -e

git fetch

git checkout origin/main -- db/backup_tsv/dpd_headwords.tsv

git checkout origin/main -- db/backup_tsv/dpd_roots.tsv

bash dps/bash/auto_commit.sh

while true; do
    echo -ne "\033[1;36m Backup Ru and SBS tables and copy them to db/backup_tsv?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            dps/scripts/backup_all_dps.py
            FILENAMES=("sbs.tsv" "russian.tsv" "ru_roots.tsv")
            for file in "${FILENAMES[@]}"; do
                cp -rf ./dps/backup/$file ./db/backup_tsv/$file
            done
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;36m Copy dpd_headwords from dps_backup to db/backup_tsv?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            cp -rf ./dps/backup/dpd_headwords.tsv ./db/backup_tsv/dpd_headwords.tsv
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;36m Rebuild db from db/backup_tsv?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            scripts/bash/build_db.sh
            dps/scripts/add_combined_view.py
            python -c "from gui.corrections_check_feedback import apply_all_suggestions; apply_all_suggestions()"
            break;;
        * )
            break;;
    esac
done


while true; do
    echo -ne "\033[1;36m Add new words?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            scripts/add/add_additions_to_db.py
            git checkout origin/main -- gui/additions.tsv
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;36m Make dpd?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            exporter/goldendict/main.py
            break;;
        * )
            break;;
    esac
done

git checkout -- pyproject.toml

git checkout -- db/backup_tsv/dpd_headwords.tsv

git checkout -- db/sanskrit/root_families_sanskrit.tsv

git checkout -- exporter/goldendict/javascript/family_compound_json.js
git checkout -- exporter/goldendict/javascript/family_idiom_json.js
git checkout -- exporter/goldendict/javascript/family_root_json.js
git checkout -- exporter/goldendict/javascript/family_set_json.js
git checkout -- exporter/goldendict/javascript/family_word_json.js


