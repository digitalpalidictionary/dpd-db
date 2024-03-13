# building components for db

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

set -e

tools/version.py

db/lookup/variants_and_spelling_mistakes.py

db/inflections/create_inflections_templates.py
db/inflections/generate_inflection_tables.py
db/inflections/transliterate_inflections.py

scripts/sanskrit_root_families_updater.py

db/families/root_family.py
db/families/word_family.py
db/families/compound_family.py
db/families/sets.py
db/families/idioms.py

scripts/anki_updater.py

db/deconstructor/sandhi_setup.py
db/deconstructor/sandhi_splitter.py
db/deconstructor/sandhi_postprocess.py
db/inflections/inflections_to_headwords.py

db/lookup/transliterate_lookup_table.py
db/lookup/help_abbrev_add_to_lookup.py

db/frequency/mapmaker.py

db/bold_defintions/update_bold_defintions_db.py

scripts/dealbreakers.py
status=$?
if [[ $status -ne  0 ]]; then
    echo "dealbreakers exited with $status. Stopping the script."
    exit $status
fi






