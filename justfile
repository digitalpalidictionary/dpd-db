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

# Run makedict in a pty (keeps ANSI colours) and save an HTML log; no transcript artifact
_logged-makedict:
    #!/usr/bin/env bash
    mkdir -p logs
    script -q -c "uv run python scripts/bash/makedict.py" /dev/null | tee >(ansi2html > "logs/makedict_$(date +"%Y-%m-%d_%H-%M-%S").html")

# Export all dictionary formats
makedict:
    just _logged-makedict

# Fast DPD-only build: turns off everything off-able, then re-enables generate components
makedict-quick:
    uv run python scripts/build/config_quick_profile.py
    just _logged-makedict
    uv run python scripts/build/config_quick_profile.py reset

# Full release export: everything on (uposatha settings), resets config to baseline after
makedict-all:
    uv run python scripts/build/config_uposatha_day.py force
    just _logged-makedict
    uv run python scripts/build/config_uposatha_reset.py force

# Minimum baseline export: resets config to baseline (post-uposatha settings) and runs
makedict-min:
    uv run python scripts/build/config_uposatha_reset.py force
    just _logged-makedict

# Complete rebuild and export everything
initial_build_db_and_export_all:
    uv run python scripts/bash/initial_build_db_and_export_all.py

# ===== DEVELOPMENT & TESTING =====

# Run pytest suite
test:
    uv run pytest tests

# Run database relationship tests
db-test:
    uv run python db_tests/db_tests_relationships.py

# Run phonetic changes test
test-phonetic:
    uv run python -m db_tests.single.add_phonetic_changes

# Find inconsistent sandhi apostrophe contractions
test-sandhi:
    uv run python db_tests/single/test_sandhi_errors.py

# ===== SUTTA ANALYSIS =====

# Stage 1 (study passage) + Stage 2 (export CSV) in sequence, interactive prompts
analyze:
    uv run python exporter/analysis/study_passage.py
    uv run python exporter/analysis/export_words_csv.py

# Add single-meaning synonyms interactively
add-synonyms-single:
    uv run python db_tests/single/add_synonym_variant_single.py

# Add multi-meaning synonyms and variants interactively
add-synonyms-multi:
    uv run python db_tests/single/add_synonym_variant_multi.py

# Find and remove or re-assign wrong synonym relationships
add-synonyms-del:
    uv run python db_tests/single/add_synonym_variant_del.py

# Find and add phonetic variant pairs to the database
add-variants-phonetic:
    uv run python db_tests/single/add_phonetic_variants.py

# Process unclassified variant field entries interactively
variants-processor:
    uv run python scripts/find/variants_process.py

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

gui:
    uv run python gui2/main.py

gui-reload:
    uv run flet run gui2/main.py -d

mkdocs:
    uv run mkdocs serve

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

# Export mobile SQLite database for DPD Flutter app
export-mobile:
    uv run python exporter/mobile/mobile_exporter.py --cone --peu --wordnet

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

# Export Apple Dictionary format only (generates XML, CSS, plist for macOS)
export-apple-dictionary:
    uv run python exporter/apple_dictionary/apple_dictionary.py

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

# ===== FINDERS =====

# Find commentary words not in the lookup table
find_comm:
    uv run python scripts/find/comm_not_in_decon_finder.py

# Count words pass2pre will surface in each Aṅguttara Nikāya book
an-remaining:
    uv run python scripts/find/pass2pre_an_counts.py

# ===== AUDIO =====

# Generate missing audio files
audio:
    uv run python audio/bhashini/generate_dpd.py

# Upload audio database release
audio-upload:
    uv run python audio/db_release_upload.py

# Download latest audio database release
audio-download:
    uv run python audio/db_release_download.py

# ===== MAINTENANCE =====

# Propagate CSS across the project
css:
    uv run python tools/css_manager.py

# Backup the database to .tsv
backup:
    uv run python db/backup_tsv/backup_dpd_headwords_and_roots.py

# Update Anki cards from the DB
anki:
    uv run exporter/anki/anki_updater.py

# Push DPD note type templates (front/back/styling) into Anki
anki-templates:
    uv run exporter/anki/template_pusher.py

# Export Vocab deck to exporter/share/dpd-anki.apkg
anki-apkg:
    uv run exporter/anki/anki_apkg_exporter.py

# Enable newsletter scraping
newsletter-on:
    uv run python -c "from tools.configger import config_update; config_update('exporter', 'make_newsletter', 'yes')"

# Disable newsletter scraping
newsletter-off:
    uv run python -c "from tools.configger import config_update; config_update('exporter', 'make_newsletter', 'no')"

# Scrape newsletters from Gmail and build docs/newsletters.md
newsletter:
    uv run python scripts/build/newsletter_scraper.py

# Reprocess all newsletters from scratch
newsletter-fresh:
    rm -f scripts/build/newsletter_processed.json
    uv run python scripts/build/newsletter_scraper.py

# Generate changelog and release notes
changelog:
    uv run python tools/docs_changelog_and_release_notes.py

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
    wget -qO- https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.xz | tar -xJ
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

# ===== CONE DICTIONARY IMPORT =====

# Extract Cone entries to TSV (includes comparison)
cone:
    uv run python scripts/extractor/extract_cone.py

# ===== CPD DICTIONARY =====

# Export CPD dictionary to GoldenDict and MDict
cpd:
    cd resources/other-dictionaries/ && uv run python dictionaries/cpd/cpd.py && cd ../..

# Scrape CPD website into data/cpd.db
cpd-scrape:
    cd resources/other-dictionaries/scrapers/cpd/ && uv run python scraper.py && cd ../../../..

# Clean and normalise cpd.db → cpd_clean.db, then diagnose
cpd-clean:
    cd resources/other-dictionaries/scrapers/cpd/ && uv run python clean.py && uv run python diagnose.py && cd ../../../..

# Inject supplementary intro pages into cpd_clean.db
cpd-extras:
    cd resources/other-dictionaries/scrapers/cpd/ && uv run python extras.py && cd ../../../..

# ===== CONFIGURATION =====

# Turn on deconstructor regeneration
decon-on:
    uv run python -c "from tools.configger import config_update; config_update('generate', 'deconstructor', 'yes')"

# Turn off deconstructor regeneration
decon-off:
    uv run python -c "from tools.configger import config_update; config_update('generate', 'deconstructor', 'no')"

# Run the Go deconstructor and sync its output into the lookup db
decon:
    go run ./go_modules/deconstructor
    uv run python scripts/build/deconstructor_output_add_to_db.py

# Run the Go frequency tables
freq:
    go run ./go_modules/frequency

# Set data limit to 100
limit100:
    uv run python -c "from tools.configger import config_update; config_update('dictionary', 'data_limit', '100')"

# Set data limit to 0 (no limit)
limit0:
    uv run python -c "from tools.configger import config_update; config_update('dictionary', 'data_limit', '0')"

# Open config.ini in fresh
config:
    fresh config.ini

# Open transcription hotwords in fresh
hotwords:
    fresh /home/bodhirasa/.config/transcribe/hotwords.txt
    transcribe -r
