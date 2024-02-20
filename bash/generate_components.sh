# building components for db

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

set -e

tools/version.py

scripts/lookup_add_variants_and_spelling_mistakes.py

inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py
families/idioms.py

scripts/anki_updater.py

sandhi/sandhi_setup.py
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py
inflections/inflections_to_headwords.py

lookup/transliterate_lookup_table.py
lookup/help_abbrev_add_to_lookup.py

frequency/mapmaker.py

bold_defintions/update_bold_defintions_db.py

scripts/dealbreakers.py
status=$?
if [[ $status -ne  0 ]]; then
    echo "dealbreakers exited with $status. Stopping the script."
    exit $status
fi






