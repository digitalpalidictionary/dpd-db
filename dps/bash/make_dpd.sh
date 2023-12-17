# update db and generate DPD for GoldenDict and unzip it locally (deva)

exec > >(tee "/home/deva/logs/mkdpd.log") 2>&1

echo "------ generate DPD for GoldenDict Started at $(date) ------"

set -e
inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py

sandhi/sandhi_setup.py
sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py

inflections/inflections_to_headwords.py
grammar_dict/grammar_dict.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py

frequency/mapmaker.py

frequency/ebt_calculation.py

dps/scripts/sbs_chapter_flag.py

dps/scripts/add_combined_view.py

exporter/exporter.py
exporter/tpr_exporter.py
exporter/deconstructor_exporter.py

ebook/ebook_exporter.py

dps/scripts/move_mdict.py

echo "------ generate DPD for GoldenDict Finished at $(date) ------"
