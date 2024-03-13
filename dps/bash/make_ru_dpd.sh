#!/usr/bin/env bash

# generate ru dpd

set -e
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'ru')"

db/families/root_family.py
db/families/word_family.py
db/families/compound_family.py
db/families/sets.py
db/families/idioms.py

echo "exporting RU DPD"

exporter/goldendict/export_gd_mdict.py

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'en')"

dps/scripts/move_mdict_ru.py

