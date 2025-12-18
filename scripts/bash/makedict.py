#!/usr/bin/env python3

"""
This script updates the database and generates DPD in all formats.
You can finely control which parts get run in ./config.ini
"""

from tools.script_runner import run_script, check_db_exists

# Check if database exists
check_db_exists()

COMMANDS = [
    # Generate components first
    "scripts/bash/generate_components.py",
    # Export to various formats
    "exporter/goldendict/main.py",
    "exporter/grammar_dict/grammar_dict.py",
    "exporter/deconstructor/deconstructor_exporter.py",
    "exporter/variants/variants_exporter.py",
    # Additional exporters
    "exporter/tpr/tpr_exporter.py",
    "exporter/kindle/kindle_exporter.py",
    "exporter/tbw/tbw_exporter.py",
    "exporter/pdf/pdf_exporter.py",
    "exporter/txt/export_txt.py",
    # Zip and tarball creation
    "scripts/build/zip_goldendict_mdict.py",
    "scripts/build/tarball_db.py",
    # Documentation updates
    "tools/docs_update_abbreviations.py",
    "tools/docs_update_bibliography.py",
    "tools/docs_update_thanks.py",
    "tools/docs_changelog_and_release_notes.py",
]

run_script("Make Dictionary", COMMANDS)
