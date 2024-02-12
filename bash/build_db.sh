# build dpd.db from scratch using backup_tsv
set -e
test -e dpd.db || touch dpd.db

scripts/db_rebuild_from_tsv.py

bash/generate_components.sh
