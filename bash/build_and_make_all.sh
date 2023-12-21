# build dpd.db for all text from scratch using backup_tsv and exporting all dictionaries, it will take few hours ti run this scripot

poetry run bash bash/initial_setup_run_once.sh

set -e
test -e dpd.db || touch dpd.db

scripts/db_rebuild_from_tsv.py
scripts/db_all_text_setup.py

poetry run bash bash/makedict.sh



