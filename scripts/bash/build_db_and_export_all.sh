# build dpd.db for from scratch using backup_tsv and export all dictionaries, 
# it will take an hour to run this script the first time

scripts/bash/initial_setup_run_once.sh

scripts/bash/build_db.sh

scripts/bash/makedict.sh



