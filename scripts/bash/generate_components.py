#!/usr/bin/env python3

"""
This script updates all tables with the latest derived data in preparation for exporting.
You can finely control which parts get run in ./config.ini
"""

from tools.script_runner import run_script, check_db_exists

# Check if database exists (replaces: if [ ! -e "dpd.db" ]; then echo "Error..."; exit 1; fi)
check_db_exists()

# List of commands to execute - all commands from the original script
COMMANDS = [
    "tools/version.py",
    "scripts/build/config_uposatha_day.py",
    "db/inflections/create_inflection_templates.py",
    "db/inflections/generate_inflection_tables.py",
    "scripts/build/root_has_verb_updater.py",
    "scripts/build/sanskrit_root_families_updater.py",
    "db/families/family_root.py",
    "db/families/family_word.py",
    "db/families/family_compound.py",
    "db/families/family_set.py",
    "db/families/family_idiom.py",
    "scripts/build/families_to_json.py",
    "scripts/build/anki_updater.py",
    "db/variants/main.py",
    "scripts/build/deconstructor_extract_archive.py",
    "scripts/build/deconstructor_output_add_to_db.py",
    "go run go_modules/deconstructor/main.go",
    "scripts/build/tarball_deconstructor_output.py",
    "scripts/build/api_ca_eva_iti_iva_hi.py",
    "db/inflections/transliterate_inflections.py",
    "db/inflections/inflections_to_headwords.py",
    "db/suttas/suttas_update.py",
    "db/suttas/suttas_to_lookup.py",
    "db/grammar/grammar_to_lookup.py",
    "db/lookup/spelling_mistakes.py",
    "db/lookup/transliterate_lookup_table.py",
    "db/lookup/help_abbrev_add_to_lookup.py",
    "scripts/build/ebt_counter.py",
    "go run go_modules/frequency/main.go",
    "db/epd/epd_to_lookup.py",
    "scripts/build/dealbreakers.py",
]

run_script("Generate Components", COMMANDS)
