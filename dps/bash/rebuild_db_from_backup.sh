# build dpd.db from scratch using dps backup_tsv

set -e
test -e dpd.db || touch dpd.db

dps/scripts/db_rebuild_from_backup.py

bash/generate_components.sh

frequency/ebt_calculation.py
dps/scripts/sbs_chapter_flag.py
dps/scripts/add_combined_view.py



