#!/usr/bin/env bash

# cheking changed words, replacing id from additions

exec > >(tee "/home/deva/logs/check_new_words.log") 2>&1

# Define color and style codes
bold=$(tput bold)
yellow=$(tput setaf 3)
green=$(tput setaf 2)
red=$(tput setaf 1)
reset=$(tput sgr0)

echo "${bold}${yellow}Filter the list of words${reset}"

dps/scripts/compare_changed_id.py

libreoffice dps/backup/for_compare/mismatched_rows.tsv

# Ask the user for confirmation
read -p "${bold}${yellow}Did you apply all changes? (y/n): ${reset}" confirmation
if [ "$confirmation" == "y" ]; then

    # Copy dpd_headwords
    cp -rf db/backup_tsv/dpd_headwords.tsv dps/backup/for_compare/dpd_headwords.tsv

    echo "${bold}${green}The job is done${reset}"
else
    echo "${bold}${red}No changes applied. Exiting.${reset}"
fi

