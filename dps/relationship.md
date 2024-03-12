Here is an explanation of the logic that determines which parameters in the config.ini allow scripts from bash to be triggered.

### always allowed :
- db/inflections/create_inflections_templates.py
- db/inflections/generate_inflection_tables.py
- db/inflections/transliterate_inflections.py
- db/inflections/inflections_to_headwords.py

### "regenerate" - "db_rebuild" :
default: `no`

At the beginning of the bash `build_db` in the beginning of the script `scripts/db_rebuild_from_tsv.py`, it is set to "yes".

it allows:

- db/deconstructor/sandhi_setup.py
- db/deconstructor/sandhi_splitter.py
- db/deconstructor/sandhi_postprocess.py

- db/families/root_family.py
- db/families/word_family.py
- db/families/compound_family.py
- db/families/sets.py

- db/frequency/mapmaker.py

At the end of the bash `build_db` in the end of the script `db/frequency/mapmaker.py`, it is set to "no".

### "exporter" - "make_dpd" :

default: `yes`

it allows:

- db/families/root_family.py
- db/families/word_family.py
- db/families/compound_family.py
- db/families/sets.py

- db/frequency/mapmaker.py

- exporter/goldendict/export_gd_mdict.py

### "exporter" - "make_deconstructor" :

default: `no`

it allows:

- db/deconstructor/sandhi_setup.py
- db/deconstructor/sandhi_splitter.py
- db/deconstructor/sandhi_postprocess.py

- exporter/deconstructor/deconstructor_exporter.py

### "exporter" - "make_grammar" :

default: `no`

it allows:

- exporter/grammar_dict/grammar_dict.py

### "exporter" - "make_tpr" :

default: `no`

it allows:

- db/deconstructor/sandhi_setup.py
- db/deconstructor/sandhi_splitter.py
- db/deconstructor/sandhi_postprocess.py

- db/families/root_family.py
- db/families/word_family.py
- db/families/compound_family.py
- db/families/sets.py

- db/frequency/mapmaker.py

- exporter/tpr/tpr_exporter.py

### "exporter" - "make_ebook" :

default: `no`

it allows:

- db/deconstructor/sandhi_setup.py
- db/deconstructor/sandhi_splitter.py
- db/deconstructor/sandhi_postprocess.py

- db/families/root_family.py
- db/families/word_family.py
- db/families/compound_family.py
- db/families/sets.py

- db/frequency/mapmaker.py

- exporter/ebook/ebook_exporter.py

