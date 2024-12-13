#!/usr/bin/env bash

# generate ru dpd

set -e

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'ru')"
python -c "from tools.configger import config_update; config_update('dictionary', 'link_url', 'https://find.dhamma.gift/bw/')"
python -c "from tools.configger import config_update; config_update('regenerate', 'freq_maps', 'yes')"

python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"


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

# dps/scripts/move_mdict_ru.py

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'en')"
python -c "from tools.configger import config_update; config_update('dictionary', 'link_url', 'http://filesrv1:8083/')"
python -c "from tools.configger import config_update; config_update('exporter', 'make_ebook', 'no')"
python -c "from tools.configger import config_update; config_update('exporter', 'make_deconstructor', 'no')"
python -c "from tools.configger import config_update; config_update('exporter', 'make_grammar', 'no')"
python -c "from tools.configger import config_update; config_update('regenerate', 'freq_maps', 'no')"


git checkout -- pyproject.toml

git checkout -- db/sanskrit/root_families_sanskrit.tsv


