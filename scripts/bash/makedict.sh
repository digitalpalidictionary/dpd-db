#!/bin/bash

# This script updates the database and generates DPD in all formats
# You can finely control which parts get run in ./config.ini 

set -e

if [ ! -e "dpd.db" ]; then
    echo "Error: dpd.db file not found."
    exit 1
fi

uv run scripts/bash/generate_components.sh

uv run exporter/grammar_dict/grammar_dict.py
uv run exporter/goldendict/main.py
uv run exporter/deconstructor/deconstructor_exporter.py

uv run exporter/tpr/tpr_exporter.py
uv run exporter/kindle/kindle_exporter.py
uv run exporter/tbw/tbw_exporter.py
uv run exporter/pdf/pdf_exporter.py
uv run exporter/variants/variants_exporter.py

uv run scripts/build/zip_goldendict_mdict.py
uv run scripts/build/tarball_db.py
uv run scripts/build/summary.py
