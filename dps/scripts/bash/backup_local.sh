
#!/bin/bash

exec > >(tee "/home/deva/logs/backup_local.log") 2>&1

# Create a temporary file to store the exclude patterns
EXCLUDE_FILE=$(mktemp)

cat > "$EXCLUDE_FILE" <<EOF
.git/
.github/
dpd.db
.venv/
.vscode/
__init__.py
.__init__.py
output/
share/
resources/
__pycache__/
EOF

# Ensure the base backup directory exists
mkdir -p "/home/deva/backups"

echo "------ Local Backup Script Started at $(date) ------"

rsync -azxi --no-links --exclude-from="$EXCLUDE_FILE" --info=progress2 --stats "/home/deva/Documents/dpd-db/" "/home/deva/backups"

echo "------ Local Backup Script Ended at $(date) ------"

# Remove the temporary exclude file
rm "$EXCLUDE_FILE"
```

Now, the script will create a temporary file, write the exclude patterns to it, and pass the file path to the `--exclude-from` option. After the backup is completed, the temporary file will be removed.

# export VISUAL=nano 
# crontab -e 