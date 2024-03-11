# setup deconstrutor to run in the cloud

poetry run python3 db/inflections/create_inflections_templates.py
poetry run python3 db/inflections/generate_inflection_tables.py
poetry run python3 db/inflections/transliterate_inflections.py
poetry run python3 db/deconstructor/sandhi_setup.py