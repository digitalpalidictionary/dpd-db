# This script builds dpd.db from scratch
# It will take an hour to run for the first time.
# WARNING! This will destroy your existing db.

set -e
test -e dpd.db || touch dpd.db

uv run scripts/build/db_rebuild_from_tsv.py

uv run db/bold_definitions/update_bold_definitions_db.py

uv run scripts/bash/generate_components.sh

# After setting db_rebuild to "yes" in db_rebuild_from_tsv.py, we change it back after the bash is done.
python -c "from tools.configger import config_update; config_update('regenerate', 'db_rebuild', 'no')"

