# generate dictionaries

set -e
python -c "from tools.configger import print_config_settings; print_config_settings()"

bash/generate_components.sh

# dps/scripts/change_ebt_count.py

grammar_dict/grammar_dict.py

exporter/exporter.py
# exporter/deconstructor_exporter.py

# exporter/tpr_exporter.py
# ebook/ebook_exporter.py

# dps/scripts/move_mdict.py

# scripts/zip_goldedict_mdict.py

# frequency/ebt_calculation.py


