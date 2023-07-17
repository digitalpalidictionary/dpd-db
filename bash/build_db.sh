set -e
# build dpd.db
test -e dpd.db || touch dpd.db
tools/configger.py

scripts/db_from_tsv.py
scripts/sbs_russian_from_tsv.py

inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py

sandhi/sandhi_setup.py --local
# run the line below to include all texts in deconstructor, it takes about 12 hours
# sandhi/sandhi_setup.py --local --all_texts
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py

frequency/mapmaker.py




