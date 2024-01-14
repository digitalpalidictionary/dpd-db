# generate dictionaries

set -e
python -c "from tools.configger import print_config_settings; print_config_settings()"

inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py

sandhi/sandhi_setup.py
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py

inflections/inflections_to_headwords.py
grammar_dict/grammar_dict.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py

frequency/mapmaker.py

dps/scripts/change_ebt_count.py

exporter/exporter.py
exporter/deconstructor_exporter.py
exporter/tpr_exporter.py

ebook/ebook_exporter.py

dps/scripts/move_mdict.py

scripts/zip_goldedict_mdict.py

frequency/ebt_calculation.py


