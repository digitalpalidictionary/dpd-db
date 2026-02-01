# DPD Database Justfile
# A handy command runner for Digital Pali Dictionary workflows

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

# Generate/update all components (requires existing db)
generate_components:
    uv run python scripts/bash/generate_components.py

# Export all dictionary formats (requires existing db)
makedict:
    uv run python scripts/bash/makedict.py

# Complete rebuild and export everything
initial_build_db_and_export_all:
    uv run python scripts/bash/initial_build_db_and_export_all.py

# ===== DEVELOPMENT & TESTING =====

# Run pytest suite
test:
    uv run pytest

# Run ruff linter on the codebase
lint:
    uv run ruff check .

# Auto-fix ruff issues where possible
lint-fix:
    uv run ruff check --fix .

# Format code with ruff
format:
    uv run ruff format .

# Show project version
version:
    uv run python tools/version.py

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

# Update suttas
suttas:
    uv run python db/suttas/suttas_update.py
    uv run python db/suttas/suttas_to_lookup.py

# Update grammar
grammar:
    uv run python db/grammar/grammar_to_lookup.py

# Update variants
variants:
    uv run python db/variants/main.py

# ===== MAINTENANCE =====

# Update project documentation
docs-update:
    uv run python tools/docs_update_abbreviations.py
    uv run python tools/docs_update_bibliography.py
    uv run python tools/docs_update_thanks.py
    uv run python tools/docs_changelog_and_release_notes.py
