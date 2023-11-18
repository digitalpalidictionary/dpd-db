# update db and generate DPD in all formats
 
set -e
inflections/create_inflections_templates.py
inflections/generate_inflection_tables.py
inflections/transliterate_inflections.py

# run the line below to run deconstructor locally
# with texts limited text set from mūla
sandhi/sandhi_setup.py --local
# run the line below to include all texts in deconstructor, it takes about 6-12 hours
# sandhi/sandhi_setup.py --local --all_texts

sandhi/sandhi_splitter.py
sandhi/sandhi_postprocess.py

inflections/inflections_to_headwords.py
grammar_dict/grammar_dict.py

families/root_family.py
families/word_family.py
families/compound_family.py
families/sets.py

frequency/mapmaker.py

exporter/exporter.py
exporter/deconstructor_exporter.py

# exporter/tpr_exporter.py
# ebook/ebook_exporter.py

scripts/anki_csvs.py
scripts/summary.py
