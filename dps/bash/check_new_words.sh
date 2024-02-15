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

    # Copy paliword
    cp -rf backup_tsv/dpd_headwords.tsv dps/backup/for_compare/dpd_headwords.tsv

    echo "${bold}${green}The job is done${reset}"
else
    echo "${bold}${red}No changes applied. Exiting.${reset}"
fi

read -p "${bold}${yellow}Did you recive additions.tsv and moved it into temp/ ? (y/n): ${reset}" confirmation
if [ "$confirmation" == "y" ]; then

    # change IDs
    dps/scripts/replace_new_id_ru_sbs.py

    echo "${bold}${green}Id's has been replaced, copy files from temp/ and rebuild DB${reset}"
else
    echo "${bold}${red}No changes applied. Exiting.${reset}"
fi
