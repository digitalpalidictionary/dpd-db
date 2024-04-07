#!/usr/bin/env bash

# generate ru dpd

set -e
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'ru')"

# scripts/bash/generate_components.sh

db/families/root_family.py
db/families/word_family.py
db/families/compound_family.py
db/families/sets.py
db/families/idioms.py

echo "exporting RU DPD"

exporter/grammar_dict/grammar_dict.py

exporter/goldendict/export_gd_mdict.py

exporter/deconstructor/deconstructor_exporter.py

exporter/ebook/ebook_exporter.py

dps/scripts/move_mdict_ru.py

# exporter/ru_components/tools/ru_zip_goldedict_mdict.py

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'en')"

git checkout -- pyproject.toml

git checkout -- db/sanskrit/root_families_sanskrit.tsv


