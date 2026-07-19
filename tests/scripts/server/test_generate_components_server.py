from scripts.server.generate_components_server import COMMANDS

# Steps the maintainer confirmed gui2 data entry does NOT use, plus
# exporter/release/config-mutation steps — none may appear in the lean list.
DROPPED = [
    "uv run pytest",
    "config_uposatha_day",
    "families_to_json",
    "anki_updater",
    "anki_apkg_exporter",
    "db/variants/main.py",
    "transliterate_inflections",
    "transliterate_lookup_table",
    "suttas_update",
    "suttas_to_lookup",
    "grammar_to_lookup",
    "help_abbrev_add_to_lookup",
    "epd_to_lookup",
    "ebt_counter",
    "frequency/main.go",
    "generate_search_index",
    "audio/",
    "dealbreakers",
]

# Steps gui2 relies on that must be present.
ESSENTIAL = [
    "db/inflections/create_inflection_templates.py",
    "db/inflections/generate_inflection_tables.py",
    "db/inflections/inflections_to_headwords.py",
    "go run go_modules/deconstructor/main.go",
    "scripts/build/deconstructor_output_add_to_db.py",
    "scripts/build/api_ca_eva_iti_iva_hi.py",
    "db/lookup/spelling_mistakes.py",
    "db/lookup/see.py",
    "db/families/family_root.py",
    "db/families/family_word.py",
    "db/families/family_compound.py",
]


def test_no_dropped_step_present():
    joined = "\n".join(COMMANDS)
    for token in DROPPED:
        assert token not in joined, f"dropped step leaked into lean list: {token}"


def test_all_essential_steps_present():
    for cmd in ESSENTIAL:
        assert cmd in COMMANDS, f"essential step missing from lean list: {cmd}"


def test_no_pytest_step():
    assert not any("pytest" in c for c in COMMANDS)


def test_deconstructor_go_precedes_its_loader():
    go = COMMANDS.index("go run go_modules/deconstructor/main.go")
    add = COMMANDS.index("scripts/build/deconstructor_output_add_to_db.py")
    assert go < add


def test_inflection_tables_precede_inflections_to_headwords():
    tables = COMMANDS.index("db/inflections/generate_inflection_tables.py")
    to_hw = COMMANDS.index("db/inflections/inflections_to_headwords.py")
    assert tables < to_hw
