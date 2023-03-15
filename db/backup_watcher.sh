#!/usr/bin/env bash

# Requires:
# sudo apt-get install inotify-tools

# The loop below watches ./*.sqlite3 files. On change, it makes a git-versioned SQL dump in a backup dir.
#
# See also:
# https://askubuntu.com/questions/819265/command-to-monitor-file-changes-within-a-directory-and-execute-command

PWD=$(pwd)
BACKUPS_DIR=backups

# Create git-versioned backup dir if it doesn't exist.
init_folder() {
    if [ ! -d "$BACKUPS_DIR" ]; then
        mkdir "$BACKUPS_DIR"
        cd "$BACKUPS_DIR" || exit
        git init && git commit -m "init" --allow-empty
        cd - || exit
    fi
}

create_backup() {
    db=$1
    name=$(basename "$db")
    sqlite3 "$db" '.dump' > "$BACKUPS_DIR/$name.sql"

    cd "$BACKUPS_DIR" || exit
    git add -A . && git commit -m "$name.sql"
    cd - || exit
}

init_folder

# Create an initial version before changes.
for file in ./*.db
do
    create_backup "$file"
done

# Start watcher.
inotifywait -m --event modify --format '%w' ./*.db | while read -r file ; do
    create_backup "$file"
done
