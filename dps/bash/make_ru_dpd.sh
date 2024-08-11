#!/usr/bin/env bash

# generate ru dpd

set -e
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'ru')"

scripts/bash/generate_components.sh

# db/families/family_root.py
# db/families/family_word.py
# db/families/family_compound.py
# db/families/family_set.py
# db/families/family_idiom.py

echo "exporting RU DPD"

exporter/grammar_dict/grammar_dict.py

exporter/goldendict/main.py

exporter/deconstructor/deconstructor_exporter.py

exporter/kindle/kindle_exporter.py

exporter/goldendict/ru_components/tools/ru_zip_goldendict_mdict.py

dps/scripts/move_mdict_ru.py

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'en')"

git checkout -- pyproject.toml

git checkout -- db/sanskrit/root_families_sanskrit.tsv


