# build dpd.db from scratch using backup_tsv
set -e
test -e dpd.db || touch dpd.db

scripts/build/db_rebuild_from_tsv.py

db/bold_definitions/update_bold_definitions_db.py

scripts/bash/generate_components.sh

# After setting db_rebuild to "yes" in db_rebuild_from_tsv.py, we change it back after the bash is done.
python -c "from tools.configger import config_update; config_update('regenerate', 'db_rebuild', 'no')"

