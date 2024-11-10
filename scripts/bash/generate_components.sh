# building components for db

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

set -e

tools/version.py

db/inflections/create_inflection_templates.py
db/inflections/generate_inflection_tables.py

scripts/build/sanskrit_root_families_updater.py

db/families/family_root.py
db/families/family_word.py
db/families/family_compound.py
db/families/family_set.py
db/families/family_idiom.py
scripts/build/families_to_json.py

scripts/build/anki_updater.py

scripts/build/deconstructor_extract_archive.py
scripts/build/deconstructor_output_add_to_db.py
go run go_modules/deconstructor/main.go

scripts/build/api_ca_evi_iti.py
db/inflections/transliterate_inflections.py
db/inflections/inflections_to_headwords.py

db/lookup/variants_and_spelling_mistakes.py
db/lookup/transliterate_lookup_table.py
db/lookup/help_abbrev_add_to_lookup.py

scripts/build/ebt_counter.py
go run go_modules/frequency/main.go 

db/epd/epd_to_lookup.py

db/rpd/rpd_to_lookup.py

scripts/build/dealbreakers.py
status=$?
if [[ $status -ne  0 ]]; then
    echo "dealbreakers exited with $status. Stopping the script."
    exit $status
fi






