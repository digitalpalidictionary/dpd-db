#!/usr/bin/env python3

from tools.script_runner import run_script

COMMANDS = [
    "tools/configger.py",
    "scripts/build/cst4_xml_to_txt.py",
    "scripts/build/transliterate_bjt.py",
    "go run go_modules/frequency/setup/*.go",
    "db/bold_definitions/extract_bold_definitions.py",
]

run_script("Initial Setup Run Once", COMMANDS)
