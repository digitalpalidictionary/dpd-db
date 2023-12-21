# update db and generate DPD in all formats

set -e

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

bash/generating_components.sh

inflections/inflections_to_headwords.py
grammar_dict/grammar_dict.py

exporter/exporter.py
exporter/deconstructor_exporter.py

exporter/tpr_exporter.py
ebook/ebook_exporter.py

scripts/zip_goldedict_mdict.py
scripts/anki_csvs.py
scripts/summary.py
