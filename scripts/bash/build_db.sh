# build dpd.db from scratch using backup_tsv
set -e
test -e dpd.db || touch dpd.db

scripts/db_rebuild_from_tsv.py

scripts/bash/generate_components.sh

db/frequency/ebt_calculation.py
