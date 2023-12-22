#!/bin/bash

exec > >(tee "/home/deva/logs/auto_commit.log") 2>&1

cd /home/deva/Documents/dpd-db/

poetry run python dps/scripts/backup_corrections_additions.py

# export VISUAL=nano 
# crontab -e 