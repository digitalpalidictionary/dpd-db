#!/usr/bin/env bash

# generate dictionaries

set -e

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'en')"
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

while true; do
    echo -ne "\033[1;36m generate_components?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            scripts/bash/generate_components.sh
            break;;
        * )
            break;;
    esac
done

dps/scripts/change_in_db/change_ebt_count.py

exporter/grammar_dict/grammar_dict.py

exporter/goldendict/main.py
exporter/deconstructor/deconstructor_exporter.py

exporter/tpr/tpr_exporter.py
exporter/kindle/kindle_exporter.py

scripts/build/zip_goldendict_mdict.py

dps/scripts/moving/move_mdict.py

git checkout -- pyproject.toml

git checkout -- db/sanskrit/root_families_sanskrit.tsv

git checkout -- shared_data/changed_templates

git checkout -- exporter/goldendict/javascript/family_compound_json.js
git checkout -- exporter/goldendict/javascript/family_idiom_json.js
git checkout -- exporter/goldendict/javascript/family_root_json.js
git checkout -- exporter/goldendict/javascript/family_set_json.js
git checkout -- exporter/goldendict/javascript/family_word_json.js





