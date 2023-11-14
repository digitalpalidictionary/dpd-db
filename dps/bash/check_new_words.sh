#!/usr/bin/env bash

# showing new words and then making fresh backup for compare

exec > >(tee "/home/deva/logs/check_new_words.log") 2>&1

# Define color and style codes
bold=$(tput bold)
yellow=$(tput setaf 3)
green=$(tput setaf 2)
red=$(tput setaf 1)
reset=$(tput sgr0)

echo "${bold}${yellow}Filter the list of words${reset}"

dps/scripts/find_new_words.py

# Ask the user for confirmation
read -p "${bold}${yellow}Did you apply all changes? (y/n): ${reset}" confirmation
if [ "$confirmation" == "y" ]; then
    
    dps/scripts/backup_all_with_history.py

    # Copy backups
    cp -rf dps/backup/* dps/backup/backup_for_compare/

    echo "${bold}${green}The job is done${reset}"
else
    echo "${bold}${red}No changes applied. Exiting.${reset}"
fi
