#!/bin/bash

# DPD Database Update & App Restart Script
# This script is intended to be run from the parent directory (e.g., ~/) on the server.

set -euo pipefail  # Exit on any error, including inside a pipe

echo "=== 1. Updating Docs Website ==="
cd digitalpalidictionary.github.io
git pull
cd ..

echo "=== 2. Entering DPD Repository ==="
cd dpd-db
echo "Current directory: $(pwd)"

# Cleared first in case a killed run left it behind.
rm -rf update_tmp
mkdir update_tmp
trap 'rm -rf update_tmp' EXIT

echo "=== 3. Updating Code from GitHub ==="
git pull --no-recurse-submodules

echo "=== 4. Updating Dependencies with uv ==="
uv sync
uv cache prune

echo "=== 5. Updating Data (Audio & Translations) ==="
uv run python audio/db_release_download.py
# uv run python resources/tipitaka_translation_db/download_and_unzip_db.py

echo "=== 6. Downloading Latest dpd.db ==="
wget -qO update_tmp/dpd.db.tar.xz https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.xz
tar -xJf update_tmp/dpd.db.tar.xz -C update_tmp
uv run python -c "import sqlite3, sys; n = sqlite3.connect(sys.argv[1]).execute('SELECT COUNT(*) FROM dpd_headwords').fetchone()[0]; sys.exit(0 if n else 'Error: new dpd.db has no headwords')" update_tmp/dpd.db
mv update_tmp/dpd.db dpd.db
uv run exporter/webapp/generate_search_index.py

echo "=== 7. Killing Uvicorn Webapp ==="
pkill -f "uvicorn exporter.webapp.main:app" || echo "No existing uvicorn process found."

# Wait a moment for ports to clear
sleep 2

# Start the app in the background using uv
# Ensure the logs directory exists in the dpd-db root
mkdir -p logs
LOG_FILE="logs/$(date '+%Y-%m-%d_%H-%M-%S').uvicorn.log"

echo "=== 8. Starting Uvicorn Webapp ==="
nohup uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 > "$LOG_FILE" 2>&1 &

echo "=== DONE ==="
echo "App started in background."
echo "Check logs with: tail -f $LOG_FILE"
ps -ef | grep uvicorn | grep -v grep

# To deploy this file, run `just dpdict-push` locally, not on the server
