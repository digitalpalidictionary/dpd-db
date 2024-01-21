# building components for db

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py
inflections/inflections_to_headwords.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py

scripts/anki_updater.py

sandhi/sandhi_setup.py
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py

frequency/mapmaker.py




