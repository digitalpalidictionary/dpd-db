#!/bin/bash

exec > >(tee "/home/deva/logs/auto_commit.log") 2>&1

cd /home/deva/Documents/dpd-db/

uv run python dps/scripts/export_from_db/backup_corrections_additions.py

while true; do
    echo -ne "\033[1;34m need to push on GitHub? \033[0m"
    read yn
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m pushing all...\033[0m"
            git push
            break;;
        *  )
            break;;
    esac
done


# export VISUAL=nano 
# crontab -e 