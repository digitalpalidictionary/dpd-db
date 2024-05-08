# building components for db

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

set -e

tools/version.py

db/inflections/create_inflections_templates.py
db/inflections/generate_inflection_tables.py
db/inflections/transliterate_inflections.py

scripts/sanskrit_root_families_updater.py

db/families/family_root.py
db/families/family_word.py
db/families/family_compound.py
db/families/family_set.py
db/families/family_idiom.py

scripts/anki_updater.py

db/deconstructor/sandhi_setup.py
db/deconstructor/sandhi_splitter.py
db/deconstructor/sandhi_postprocess.py
db/inflections/inflections_to_headwords.py

db/lookup/variants_and_spelling_mistakes.py
db/lookup/transliterate_lookup_table.py
db/lookup/help_abbrev_add_to_lookup.py

db/frequency/mapmaker.py

db/bold_definitions/update_bold_definitions_db.py

db/epd/epd_to_lookup.py

scripts/dealbreakers.py
status=$?
if [[ $status -ne  0 ]]; then
    echo "dealbreakers exited with $status. Stopping the script."
    exit $status
fi






