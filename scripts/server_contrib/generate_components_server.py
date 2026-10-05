"""Lean component rebuild for the contributor web server.

A strict, reordered SUBSET of `scripts/bash/generate_components.py` that
populates only the tables/columns the interactive gui2 app actually reads
during data entry. Everything that exists solely for exporters, release
artifacts, or db columns gui2 never queries is dropped, cutting the nightly
rebuild substantially.

WHAT gui2 READS (verified 2026-07-19 against the gui2 source):
  - dpd_headwords / dpd_roots (core; from db_rebuild_from_tsv, not here)
  - lookup.lookup_key + lookup.headwords  (word / Ctrl+F lookup)
  - lookup.deconstructor                  (compound / sandhi lookup)
  - lookup.spelling                        (pass2pre filtering)
  - inflection_templates.pattern + dpd_headwords.inflections/inflections_html
  - family_root/word/compound name columns (dropdowns / validation)

DROPPED (maintainer-confirmed 2026-07-19 as unused by gui2 data entry):
  - transliterate_inflections / transliterate_lookup_table (no non-roman input)
  - grammar_to_lookup, epd_to_lookup, help_abbrev_add_to_lookup,
    suttas_update, suttas_to_lookup  (lookup columns / sutta_info gui2 never reads)
  - ebt_counter + frequency (freq_html/ebt_count are cosmetic, deferred)
  - anki, audio, variants, search_index, families_to_json, dealbreakers,
    config_uposatha_day  (exporter / release / config-mutation only)

NO pytest step: the lean db intentionally omits data the full suite asserts on,
and the pulled code is already CI-tested. The post-rebuild gate is the
maintenance-window health check (row-count bounds) in maintenance_window.py.

Keep this list in sync with `scripts/bash/generate_components.py` when build
steps that touch gui2-read data are added or reordered.
"""

from tools.script_runner import check_db_exists, run_script

# Order matches generate_components.py; only gui2-essential steps are kept.
COMMANDS = [
    "tools/logo.py",
    "tools/version.py",
    "db/inflections/create_inflection_templates.py",
    "db/inflections/generate_inflection_tables.py",
    "scripts/build/root_has_verb_updater.py",
    "scripts/build/sanskrit_root_families_updater.py",
    "db/families/family_root.py",
    "db/families/family_word.py",
    "db/families/family_compound.py",
    "db/families/family_set.py",
    "db/families/family_idiom.py",
    "go run go_modules/deconstructor/main.go",
    "scripts/build/deconstructor_output_add_to_db.py",
    "scripts/build/api_ca_eva_iti_iva_hi.py",
    "db/inflections/inflections_to_headwords.py",
    "db/lookup/see.py",
    "db/lookup/spelling_mistakes.py",
]


if __name__ == "__main__":
    check_db_exists()
    run_script("Generate Components (server, lean)", COMMANDS)
