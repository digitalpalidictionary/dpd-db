
set -e

# setup config.ini file
tools/configger.py

# setup CST texts for frequency mapping
db/frequency/cst4_xml_to_txt.py
db/frequency/corpus_counter.py

# setup bold definitions database
db/bold_defintions/extract_bold_definitions.py
