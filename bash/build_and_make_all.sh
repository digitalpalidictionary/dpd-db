# build dpd.db for all text from scratch using backup_tsv and exporting all dictionaries, it will take few hours ti run this scripot

poetry run bash bash/initial_setup_run_once.sh

set -e
test -e dpd.db || touch dpd.db

scripts/db_rebuild_from_tsv.py
scripts/db_all_text_setup.py

inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py
inflections/inflections_to_headwords.py

sandhi/sandhi_setup.py
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py

frequency/mapmaker.py

grammar_dict/grammar_dict.py
exporter/exporter.py
exporter/deconstructor_exporter.py

exporter/tpr_exporter.py
ebook/ebook_exporter.py



