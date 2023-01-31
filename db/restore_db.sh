#!/usr/bin/env sh

# Usage:
#
# In the dpd-backups folder, checkout the db file at the commit where you want
# to restore from, then use this script.
#
# ./scripts/restore_db.sh dpd-new.sqlite3 ../dpd-backups/dpd.sqlite3.sql

NEW_DB_FILE="$1"
DB_DUMP_SQL="$2"

cat "$DB_DUMP_SQL" | sqlite3 "$NEW_DB_FILE"
