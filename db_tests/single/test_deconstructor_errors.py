#!/usr/bin/env python3

"""Test the deconstructor column in the lookup table:
every value must be valid JSON and contain only Pāḷi alphabet
characters, spaces and +. Run after regenerating the deconstructor."""

import json

from rich import print

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def parse_deconstructions(json_str: str) -> list[str] | None:
    """Parse a deconstructor JSON string, or return None if invalid."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def main() -> None:
    pr.yellow_title("find errors in deconstructions")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    pr.green_tmr("db lookup")
    db = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
    pr.yes(len(db))

    error_letters: dict[str, str] = {}

    pali_alphabet_plus = pali_alphabet + [" ", "+"]

    pr.green_title("find errors")

    for counter, i in enumerate(db):
        if counter % 100000 == 0 and counter != 0:
            pr.counter(counter, len(db), i.lookup_key)

        deconstructions = parse_deconstructions(i.deconstructor)
        if deconstructions is None:
            pr.red(f"{i.lookup_key} invalid JSON in deconstructor")
            continue
        for decon in deconstructions:
            for letter in decon:
                if letter not in pali_alphabet_plus:
                    error_letters[i.lookup_key] = letter
                    pr.red(f"{i.lookup_key} invalid letter: {letter} ")

    print(error_letters)


if __name__ == "__main__":
    main()
