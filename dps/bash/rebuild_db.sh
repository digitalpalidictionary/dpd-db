# build dpd.db from scratch using backup_tsv
set -e

scripts/db_rebuild_from_tsv.py

inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py

sandhi/sandhi_setup.py
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py

frequency/mapmaker.py

frequency/ebt_calculation.py
dps/scripts/sbs_chapter_flag.py
dps/scripts/add_combined_view.py



