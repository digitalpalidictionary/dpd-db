#!/usr/bin/env python3

"""
First-time setup: make the config file, convert and transliterate the source
texts, build the frequency maps and extract the bold definitions.
Run once on a fresh checkout. CI also runs it.
"""

from tools.script_runner import run_script

COMMANDS: list[str] = [
    "tools/logo.py",
    # setup config.ini file
    "tools/configger.py",
    # convert CST xml to txt
    "scripts/build/cst4_xml_to_txt.py",
    # transliterate BJT files and save to json and txt
    "scripts/build/transliterate_bjt.py",
    # make frequency maps of all the Pāḷi texts
    "go run ./go_modules/frequency/setup",
    # setup bold definitions database
    "db/bold_definitions/extract_bold_definitions.py",
]


def main() -> None:
    """Run every setup step in order."""
    run_script("Initial Setup Run Once", COMMANDS)


if __name__ == "__main__":
    main()
