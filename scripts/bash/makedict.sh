#!/bin/bash

# This script updates the database and generates DPD in all formats
# You can finely control which parts get run in ./config.ini 

set -e

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

start_time=$(date +%s)
echo "$(date -d @$start_time)"

uv run scripts/bash/generate_components.sh

uv run exporter/goldendict/main.py
uv run exporter/grammar_dict/grammar_dict.py
uv run exporter/deconstructor/deconstructor_exporter.py
uv run exporter/variants/variants_exporter.py

uv run exporter/tpr/tpr_exporter.py
uv run exporter/kindle/kindle_exporter.py
uv run exporter/tbw/tbw_exporter.py
uv run exporter/pdf/pdf_exporter.py
uv run exporter/txt/export_txt.py

uv run scripts/build/zip_goldendict_mdict.py
uv run scripts/build/tarball_db.py

uv run tools/docs_update_abbreviations.py
uv run tools/docs_update_bibliography.py
uv run tools/docs_update_thanks.py
uv run tools/docs_changelog_and_release_notes.py

end_time=$(date +%s)
elapsed=$((end_time - start_time))
elapsed_min=$((elapsed / 60))
echo "$elapsed_min minutes"
