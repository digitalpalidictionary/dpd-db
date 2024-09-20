# build dpd.db for from scratch using backup_tsv and export all dictionaries, 
# it will take an hour to run this script the first time

scripts/bash/initial_setup_run_once.sh

set -e
test -e dpd.db || touch dpd.db

scripts/db_rebuild_from_tsv.py

db/bold_definitions/update_bold_definitions_db.py

scripts/bash/makedict.sh



