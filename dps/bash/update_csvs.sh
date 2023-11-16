#!/usr/bin/env bash

# apply changes from dps.ods into db 
# extract csv for anki and db-browser with frequency

# if update from dps:
# dps/scripts/archive/ods2csv.py
# dps/scripts/archive/sbs_russian_from_csv.py

# from db into csvs:
dps/scripts/dps_csv.py
dps/scripts/anki_csvs.py
# dps/scripts/insert_freq_ebt.py

# dps/scripts/save_concise_txt.py

