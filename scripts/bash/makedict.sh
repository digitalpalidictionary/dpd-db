# update db and generate DPD in all formats

set -e

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

scripts/config_uposatha_day.py
scripts/bash/generate_components.sh

exporter/grammar_dict/grammar_dict.py
exporter/goldendict/export_gd_mdict.py
exporter/deconstructor/deconstructor_exporter.py

exporter/tpr/tpr_exporter.py
exporter/ebook/ebook_exporter.py
exporter/tbw/tbw_exporter.py

scripts/zip_goldendict_mdict.py
scripts/tarball_db.py
scripts/summary.py
