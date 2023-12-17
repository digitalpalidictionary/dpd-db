Here is an explanation of the logic that determines which parameters in the config.ini allow scripts from bash to be triggered.

### always allowed :
- inflections/create_inflections_templates.py
- inflections/generate_inflection_tables.py
- inflections/transliterate_inflections.py
- inflections/inflections_to_headwords.py

### "regenerate" - "db_rebuild" :
default: `no`

At the beginning of the bash `build_db` in the beginning of the script `scripts/db_rebuild_from_tsv.py`, it is set to "yes".

it allows:

- sandhi/sandhi_setup.py
- sandhi/sandhi_splitter.py
- sandhi/sandhi_postprocess.py

- families/root_family.py
- families/word_family.py
- families/compound_family.py
- families/sets.py

- frequency/mapmaker.py

At the end of the bash `build_db` in the end of the script `frequency/mapmaker.py`, it is set to "no".

### "exporter" - "make_dpd" :

default: `yes`

it allows:

- families/root_family.py
- families/word_family.py
- families/compound_family.py
- families/sets.py

- frequency/mapmaker.py

- exporter/exporter.py

### "exporter" - "make_deconstructor" :

default: `no`

it allows:

- sandhi/sandhi_setup.py
- sandhi/sandhi_splitter.py
- sandhi/sandhi_postprocess.py

- exporter/deconstructor_exporter.py

### "exporter" - "make_grammar" :

default: `no`

it allows:

- grammar_dict/grammar_dict.py

### "exporter" - "make_tpr" :

default: `no`

it allows:

- sandhi/sandhi_setup.py
- sandhi/sandhi_splitter.py
- sandhi/sandhi_postprocess.py

- families/root_family.py
- families/word_family.py
- families/compound_family.py
- families/sets.py

- frequency/mapmaker.py

- exporter/tpr_exporter.py

### "exporter" - "make_ebook" :

default: `no`

it allows:

- sandhi/sandhi_setup.py
- sandhi/sandhi_splitter.py
- sandhi/sandhi_postprocess.py

- families/root_family.py
- families/word_family.py
- families/compound_family.py
- families/sets.py

- frequency/mapmaker.py

- ebook/ebook_exporter.py

