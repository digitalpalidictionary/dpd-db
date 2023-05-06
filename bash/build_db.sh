set -e
# setup cst texts
frequency/cst4_xml_to_txt.py
frequency/corpus_counter.py
# build dpd
test -e dpd.db || touch dpd.db
db/db_from_tsv.py
scripts/sbs_russian_from_tsv.py
inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py
families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py
frequency/mapmaker.py
sandhi/sandhi_setup.py
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py
