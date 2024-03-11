#!/usr/bin/env bash

# making backup of db if it is first time today and open GUI

exec > >(tee "/home/deva/logs/gui.log") 2>&1

# Directory where backups are stored
BACKUP_DIR="dps/backup/"

# Get today's date
TODAY=$(date "+%Y-%m-%d")

# Check the modification date of a file (for example, dpd_headwords.tsv)
FILE_DATE=$(stat -c %y "${BACKUP_DIR}dpd_headwords.tsv" | cut -d' ' -f1)

# Check if backups for today exist in db/backup_tsv/
if [[ "$FILE_DATE" == "$TODAY" ]]; then
    echo "Backups for today already exist."
else
    dps/scripts/backup_all_dps.py
fi

# Run the GUI script
gui/gui.py
