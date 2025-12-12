#!/usr/bin/env python3

"""
This script builds dpd.db from scratch.
It will take an hour to run for the first time.
WARNING! This will destroy your existing db.
"""

from tools.script_runner import run_script, touch_file
from tools.configger import config_update

# Create db file if it doesn't exist
touch_file("dpd.db")

# List of commands to execute
COMMANDS = [
    "scripts/build/db_rebuild_from_tsv.py",
    "db/bold_definitions/update_bold_definitions_db.py",
    "scripts/bash/generate_components.py",
]

run_script("Initial Build DB", COMMANDS)
config_update("regenerate", "db_rebuild", "no")
