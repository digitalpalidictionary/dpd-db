#!/usr/bin/env python3

"""Find errors in deconstructions."""

import json

from rich import print

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def is_valid_json(json_str: str) -> tuple[bool, list[str] | None]:
    """Validate if a string is valid JSON.
    Return bool and json or Non
    """
    try:
        parsed = json.loads(json_str)
        return True, parsed
    except json.JSONDecodeError:
        return False, None


def main():
    pr.title("find errors in deconstructions")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    pr.green("db lookup")
    db = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
    pr.yes(len(db))

    error_letters = {}

    pali_alphabet_plus = pali_alphabet + [" ", "+"]

    pr.green_title("find errors")

    for counter, i in enumerate(db):
        if counter % 100000 == 0 and counter != 0:
            pr.counter(counter, len(db), i.lookup_key)

        is_valid, parsed_json = is_valid_json(i.deconstructor)
        if not is_valid:
            pr.error(f"{i.lookup_key} invalid JSON in deconstructor")
        if parsed_json:
            for decon in parsed_json:
                for letter in decon:
                    if letter not in pali_alphabet_plus:
                        error_letters[i.lookup_key] = letter
                        pr.error(f"{i.lookup_key} invalid letter: {letter} ")

    print(error_letters)


if __name__ == "__main__":
    main()
