
set -e

# setup config.ini file
tools/configger.py

# setup CST texts for frequency mapping
frequency/cst4_xml_to_txt.py
frequency/corpus_counter.py

# setup bold definitions database
bold_defintions/extract_bold_definitions.py
