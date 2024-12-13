#!/usr/bin/env bash

# generate dictionaries

set -e

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'en')"
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

scripts/bash/generate_components.sh

dps/scripts/change_ebt_count.py

exporter/grammar_dict/grammar_dict.py

exporter/goldendict/main.py
exporter/deconstructor/deconstructor_exporter.py

exporter/tpr/tpr_exporter.py
exporter/kindle/kindle_exporter.py

scripts/build/zip_goldendict_mdict.py

dps/scripts/move_mdict.py

git checkout -- pyproject.toml

git checkout -- db/sanskrit/root_families_sanskrit.tsv

git checkout -- exporter/goldendict/javascript/family_compound_json.js
git checkout -- exporter/goldendict/javascript/family_idiom_json.js
git checkout -- exporter/goldendict/javascript/family_root_json.js
git checkout -- exporter/goldendict/javascript/family_set_json.js
git checkout -- exporter/goldendict/javascript/family_word_json.js




