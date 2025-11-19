#!/bin/bash

# This script updates all tables with the latest derived data in preparation for exporting.
# You can finely control which parts get run in ./config.ini 

set -e

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

uv run python tools/version.py
uv run scripts/build/config_uposatha_day.py

uv run python db/inflections/create_inflection_templates.py
uv run python db/inflections/generate_inflection_tables.py

uv run python scripts/build/root_has_verb_updater.py
uv run python scripts/build/sanskrit_root_families_updater.py

uv run python db/families/family_root.py
uv run python db/families/family_word.py
uv run python db/families/family_compound.py
uv run python db/families/family_set.py
uv run python db/families/family_idiom.py
uv run python scripts/build/families_to_json.py

uv run python scripts/build/anki_updater.py

uv run python db/variants/main.py 

uv run db/suttas/suttas_update.py
uv run db/suttas/sutta_to_lookup.py

uv run python scripts/build/deconstructor_extract_archive.py
uv run python scripts/build/deconstructor_output_add_to_db.py
go run go_modules/deconstructor/main.go
uv run python scripts/build/tarball_deconstructor_output.py

uv run python scripts/build/api_ca_eva_iti_iva_hi.py
uv run python db/inflections/transliterate_inflections.py
uv run python db/inflections/inflections_to_headwords.py

uv run python db/grammar/grammar_to_lookup.py

uv run python db/lookup/spelling_mistakes.py

uv run python db/lookup/transliterate_lookup_table.py
uv run python db/lookup/help_abbrev_add_to_lookup.py

uv run python scripts/build/ebt_counter.py
go run go_modules/frequency/main.go

uv run python db/epd/epd_to_lookup.py

uv run python scripts/build/dealbreakers.py
status=$?
if [[ $status -ne  0 ]]; then
    echo "dealbreakers exited with $status. Stopping the script."
    exit $status
fi
