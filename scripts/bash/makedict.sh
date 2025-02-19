# This script updates the database and generates DPD in all formats
# You can finely control which parts get run in ./config.ini 

set -e

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

scripts/build/config_uposatha_day.py
scripts/bash/generate_components.sh

exporter/grammar_dict/grammar_dict.py
exporter/goldendict/main.py
exporter/deconstructor/deconstructor_exporter.py

# experimental variants dict
db/variants/extract_variants_main.py 

exporter/tpr/tpr_exporter.py
exporter/kindle/kindle_exporter.py
exporter/tbw/tbw_exporter.py
exporter/pdf/pdf_exporter.py

scripts/build/zip_goldendict_mdict.py
scripts/build/tarball_db.py
scripts/build/summary.py
