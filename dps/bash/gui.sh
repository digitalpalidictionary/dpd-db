#!/usr/bin/env bash

# making backup of db if it is first time today and open GUI

exec &> 'temp/.gui_errors.txt'

# Check if backups for today exist in dps/backup/
if ls dps/backup/*$(date +"%Y%m%d")*.tsv 1> /dev/null 2>&1; then
    echo "Backups for today already exist."
else
    dps/scripts/backup_all_with_history.py
fi

# Run the GUI script
gui/gui.py
