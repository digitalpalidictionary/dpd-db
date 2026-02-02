# DPD Database Justfile
# A handy command runner for Digital Pāḷi Dictionary workflows

# Default recipe shows available commands
default:
    @just --list

# ===== HIGH-LEVEL WORKFLOWS (match script names) =====

# Full initial setup (run once)
initial_setup_run_once:
    uv run python scripts/bash/initial_setup_run_once.py

# Build database from scratch (WARNING: destroys existing db)
initial_build_db:
    uv run python scripts/bash/initial_build_db.py

# Generate/update all components
generate_components:
    uv run python scripts/bash/generate_components.py

# Export all dictionary formats
makedict:
    #!/usr/bin/env bash
    mkdir -p logs
    timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    script -q -c "uv run python scripts/bash/makedict.py" | tee >(ansi2html > "logs/makedict_$timestamp.html")

# Complete rebuild and export everything
initial_build_db_and_export_all:
    uv run python scripts/bash/initial_build_db_and_export_all.py

# ===== DEVELOPMENT & TESTING =====

# Run pytest suite
test:
    uv run pytest tests

# Run ruff linter and formatter (excludes archive/ and resources/)
lint:
    uv run ruff check . --exclude archive --exclude resources
    uv run ruff format . --exclude archive --exclude resources

# Show project version
version:
    uv run python tools/version.py

# Start the webapp server
webapp:
    uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir exporter/webapp

# ===== INDIVIDUAL EXPORTERS (run after generate) =====

# Export GoldenDict format only
export-goldendict:
    uv run python exporter/goldendict/main.py

# Export Kindle format only
export-kindle:
    uv run python exporter/kindle/kindle_exporter.py

# Export grammar dictionary only
export-grammar:
    uv run python exporter/grammar_dict/grammar_dict.py

# Export deconstructor only
export-deconstructor:
    uv run python exporter/deconstructor/deconstructor_exporter.py

# Export variants only
export-variants:
    uv run python exporter/variants/variants_exporter.py

# Export TPR data for Tipitaka Pali Reader
export-tpr:
    uv run python exporter/tpr/tpr_exporter.py

# Export TBW format only
export-tbw:
    uv run python exporter/tbw/tbw_exporter.py

# Export SuttaCentral format only
export-sc:
    uv run python exporter/sutta_central/sutta_central_exporter.py

# Export PDF format only
export-pdf:
    uv run python exporter/pdf/pdf_exporter.py

# Export plain text only
export-txt:
    uv run python exporter/txt/export_txt.py

# Build WXT browser extension package
wxt:
    @cd exporter/wxt_extension && npm run package

# ===== DATABASE COMPONENTS =====

# Regenerate inflection tables
inflections:
    uv run python db/inflections/create_inflection_templates.py
    uv run python db/inflections/generate_inflection_tables.py

# Update all families
families:
    uv run python db/families/family_root.py
    uv run python db/families/family_word.py
    uv run python db/families/family_compound.py
    uv run python db/families/family_set.py
    uv run python db/families/family_idiom.py

# ===== AUDIO =====
# Generate missing audio files
audio:
    uv run python audio/bhashini/generate_dpd.py

# ===== MAINTENANCE =====

# Backup the database to .tsv
backup:
    uv run python db/backup_tsv/backup_dpd_headwords_and_roots.py

# Update project documentation
docs-update:
    uv run python tools/docs_update_abbreviations.py
    uv run python tools/docs_update_bibliography.py
    uv run python tools/docs_update_thanks.py
    uv run python tools/docs_changelog_and_release_notes.py

# Open most recent log file in browser
showlog:
    #!/usr/bin/env bash
    latest_file=$(ls -t logs/* | head -1)
    xdg-open "$latest_file"

# ===== SERVER =====

# Complete server update: code, data, db, search index, restart
server-update:
    #!/usr/bin/env bash
    set -e
    git pull
    uv sync
    uv run python audio/db_release_download.py
    wget -qO- https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.bz2 | tar -xj
    uv run exporter/webapp/generate_search_index.py
    pkill -f "uvicorn exporter.webapp.main:app" || true
    sleep 2
    mkdir -p logs
    nohup uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 > "logs/$(date '+%Y-%m-%d_%H-%M-%S').uvicorn.log" 2>&1 &

# Quick reload: pull code and restart server
server-reload:
    #!/usr/bin/env bash
    git pull
    pkill -f "uvicorn exporter.webapp.main:app" || true
    sleep 2
    mkdir -p logs
    nohup uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 > "logs/$(date '+%Y-%m-%d_%H-%M-%S').uvicorn.log" 2>&1 &
