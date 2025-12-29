#!/bin/bash

# DPD Database Update & App Restart Script
# This script is intended to be run from the parent directory (e.g., ~/) on the server.

set -e  # Exit immediately if a command exits with a non-zero status

echo "=== 1. Entering DPD Repository ==="
cd dpd-db
echo "Current directory: $(pwd)"

echo "=== 2. Updating Code from GitHub ==="
git pull

echo "=== 3. Updating Dependencies with uv ==="
uv sync

echo "=== 4. Updating Data (Audio & Translations) ==="
uv run python audio/db_release_download.py
# uv run python resources/tipitaka_translation_db/download_and_unzip_db.py

echo "=== 5. Downloading Latest dpd.db ==="
wget -qO- https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.bz2 | tar -xj
if [ ! -f dpd.db ]; then
    echo "Error: dpd.db not found after extraction"
    exit 1
fi

echo "=== 6. Killing Uvicorn Webapp ==="
pkill -f "uvicorn exporter.webapp.main:app" || echo "No existing uvicorn process found."

# Wait a moment for ports to clear
sleep 2

# Start the app in the background using uv
# Ensure the logs directory exists in the dpd-db root
mkdir -p logs
LOG_FILE="logs/$(date '+%Y-%m-%d').uvicorn.log"

echo "=== 7. Starting Uvicorn Webapp ==="
nohup uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 > "$LOG_FILE" 2>&1 &

echo "=== DONE ==="
echo "App started in background."
echo "Check logs with: tail -f $LOG_FILE"
ps -ef | grep uvicorn | grep -v grep