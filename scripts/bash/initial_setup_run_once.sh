
set -e

# setup config.ini file
tools/configger.py

# convert CST xml to txt
scripts/build/cst4_xml_to_txt.py

# transliterate BJT files and save to json and txt
scripts/build/transliterate_bjt.py

# make frequency maps of all the Pāḷi texts
go run go_modules/frequency/setup/*.go

# setup bold definitions database
db/bold_definitions/extract_bold_definitions.py

