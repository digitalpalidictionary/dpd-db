#!/usr/bin/env python3

"""
This script builds dpd.db from scratch.
It will take an hour to run for the first time.
WARNING! This will destroy your existing db.
"""

from tools.configger import config_update
from tools.paths import ProjectPaths
from tools.script_runner import run_script, touch_file

# List of commands to execute
COMMANDS: list[str] = [
    "tools/logo.py",
    "scripts/build/db_rebuild_from_tsv.py",
    "db/bold_definitions/update_bold_definitions_db.py",
    "scripts/bash/generate_components.py",
]


def main() -> None:
    """Create the db file if missing, rebuild it, then reset the rebuild flag."""
    pth = ProjectPaths()
    touch_file(str(pth.dpd_db_path))
    run_script("Initial Build DB", COMMANDS)
    config_update("regenerate", "db_rebuild", "no")


if __name__ == "__main__":
    main()
