# build dpd.db from scratch using backup_tsv
set -e
test -e dpd.db || touch dpd.db

scripts/db_rebuild_from_tsv.py

db/bold_definitions/update_bold_definitions_db.py

scripts/bash/generate_components.sh
