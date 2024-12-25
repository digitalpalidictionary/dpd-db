#!/usr/bin/env bash

# replacing id from additions, cheking changed words

exec > >(tee "/home/deva/logs/check_new_words.log") 2>&1

while true; do
    echo -ne "\033[1;36m backup all dps?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            dps/scripts/backup_all_dps.py
            break;;
        * )
            break;;
    esac
done



# Define color and style codes
bold=$(tput bold)
yellow=$(tput setaf 3)
green=$(tput setaf 2)
red=$(tput setaf 1)
reset=$(tput sgr0)

echo "${bold}${yellow}Filter the list of words${reset}"

libreoffice gui/delated_words_history.tsv

dps/scripts/compare_changed_id.py

libreoffice dps/backup/for_compare/added_another_meaning.tsv

libreoffice dps/backup/for_compare/changed_notes.tsv

# Ask the user for confirmation
read -p "${bold}${yellow}Did you apply all changes? (y/n): ${reset}" confirmation
if [ "$confirmation" == "y" ]; then

    # Copy dpd_headwords
    cp -rf db/backup_tsv/dpd_headwords.tsv dps/backup/for_compare/dpd_headwords.tsv

    echo "${bold}${green}The job is done${reset}"
else
    echo "${bold}${red}No changes applied. Exiting.${reset}"
fi

scripts/backup/backup_ru_sbs.py

dps/scripts/replace_new_id.py