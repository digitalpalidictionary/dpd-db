#!/usr/bin/env bash

# generate dictionaries

set -e
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

# allow exporter_ru.py use functions from exporter.py
export PYTHONPATH=/home/deva/Documents/dpd-db/exporter:$PYTHONPATH

# to avoid warning py pyright add to .vscode/settings.json:
# { "python.analysis.extraPaths": ["/home/deva/Documents/dpd-db/exporter"] }

# bash/generate_components.sh

# dps/scripts/change_ebt_count.py

# grammar_dict/grammar_dict.py

dps/exporter_ru/exporter_ru.py

# exporter/deconstructor_exporter.py

# exporter/tpr_exporter.py
# ebook/ebook_exporter.py

dps/scripts/move_mdict_ru.py