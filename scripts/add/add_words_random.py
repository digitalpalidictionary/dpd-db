#!/usr/bin/env python3

"""Find a random word
- without meaning_1
- without example_1
"""

from random import randrange
import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import p_title


def main():

    """Compile a list of words that are
    - without meaning_1
    - without example_1"""

    p_title("pick a random word to add")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    no_meaning: list = []
    no_example: list = []
    all_missing: list = []

    for i in db:
        if not i.meaning_1:
            no_meaning.append(i.id)
        if not i.example_1:
            no_example.append(i.id)
    
    all_missing.extend(no_example)
    all_missing.extend(no_meaning)
    print(len(set(all_missing)))
    
    user_input = ""
    while user_input != "x":
        random_number = randrange(len(all_missing))
        random_id = all_missing[random_number]
        word = db_session.query(DpdHeadword).filter_by(id=random_id).first()
        pyperclip.copy(word.lemma_1)
        print(word)
        user_input = input()


if __name__ == "__main__":
    main()
