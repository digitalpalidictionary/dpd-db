#!/usr/bin/env python3

"""
This script builds dpd.db from scratch and export all dictionaries.
It will take an hour to run for the first time.
WARNING! This will destroy your existing db.
"""

from tools.script_runner import run_script

# List of commands - calls the other converted scripts
COMMANDS = [
    "scripts/bash/initial_setup_run_once.py",
    "scripts/bash/initial_build_db.py",
    "scripts/bash/makedict.py",
]

# Run the complete workflow with timing
run_script("Initial Build DB and Export All", COMMANDS)
