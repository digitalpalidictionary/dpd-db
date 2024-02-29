#!/usr/bin/env bash

# generate dictionaries

set -e
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

bash/generate_components.sh

dps/scripts/change_ebt_count.py

grammar_dict/grammar_dict.py

exporter/exporter.py
exporter/deconstructor_exporter.py

exporter/tpr_exporter.py
ebook/ebook_exporter.py

dps/scripts/move_mdict.py

# Check if the configuration setting
if python -c "from tools.configger import config_test; result = config_test('dictionary', 'show_ebt_count', 'no'); print('show_ebt_count is False') if result == 'no' else exit(not result)"; then
    # Do nothing if the condition is False
    echo 'scripts/zip_goldedict_mdict.py and frequency/ebt_calculation.py are disabled'
else
    # Run if the condition is True
    scripts/zip_goldedict_mdict.py
    frequency/ebt_calculation.py
fi

# Update the show_ebt_count setting to 'no' if it was 'yes'
if python -c "from tools.configger import config_test; exit(not config_test('dictionary', 'show_ebt_count', 'yes'))"; then

    python -c "from tools.configger import config_update; config_update('dictionary', 'show_ebt_count', 'no')"

fi

git checkout -- pyproject.toml

git checkout -- sanskrit/root_families_sanskrit.tsv