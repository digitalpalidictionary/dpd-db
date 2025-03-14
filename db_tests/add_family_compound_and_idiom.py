"""
Add missing family compounds and idioms from
negative Pāḷi words.
"""

import re
from rich import print
import pyperclip

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound, FamilyIdiom
from tools.paths import ProjectPaths
from tools.goldendict_tools import open_in_goldendict_os
from tools.printer import p_title

neg_exceptions = [4, 385, 386, 387, 2017, 3444, 3445, 3446, 3447]


def make_family_compound_and_idiom_set(db_session):
    """Make a set of all existing family compounds and idioms."""
    fc_set = set()

    results_fc = db_session.query(FamilyCompound).all()
    results_fc: list[FamilyCompound]
    fc_set = {i.compound_family for i in results_fc}

    results_id = db_session.query(FamilyIdiom).all()
    results_id: list[FamilyIdiom]
    fc_set |= {i.idiom for i in results_id}

    return fc_set


def make_positive(i: DpdHeadword):
    """Logically creates a positive version of a negative Pāḷi word."""

    print(i)
    print()

    positive = None

    if len(i.lemma_clean) > 2:
        if i.lemma_clean.startswith("na"):
            # find double consonants
            if i.lemma_clean[2] == i.lemma_clean[3]:
                positive = i.lemma_clean[3:]
            else:
                positive = i.lemma_clean[2:]

        elif i.lemma_clean.startswith("an"):
            # check construction doesn't start with "n"
            if re.sub("^na > an + ", "", i.construction).startswith("n"):
                positive = i.lemma_clean[2:]
            else:
                positive = i.lemma_clean[2:]

        elif i.lemma_clean.startswith("nā"):
            # from third letter onwards with preceding a
            positive = f"a{i.lemma_clean[2:]}"

        elif i.lemma_clean.startswith("a"):
            # find double consonants
            if i.lemma_clean[1] == i.lemma_clean[2]:
                positive = i.lemma_clean[2:]
            # check construction doesn't start with "n"
            elif re.sub("^a + ", "", i.construction).startswith("n"):
                positive = i.lemma_clean[1:]
            else:
                positive = i.lemma_clean[1:]

    return positive


def router(counter, total_counter, i, positive, fc_set, db_session):
    print()
    print(f"{'counter':<20}[green]{counter} / {total_counter}")
    print(f"{'id':<20}[green]{i.id}")
    print(f"{'lemma_1':<20}[green]{i.lemma_1} [white]{i.meaning_1}")
    print(f"{'positive':<20}[green]{positive}")
    print(f"{'exists':<20s}[green]{positive in fc_set}")
    open_in_goldendict_os(positive)

    print()
    print("Add positive? 1: yes 2: manual 3: commit ", end="")
    pyperclip.copy(positive)
    fc_choice = input()
    if fc_choice == "1":
        i.family_compound = positive
        i.family_idioms = positive
        return False

    elif fc_choice == "2":
        print("What is the family compound and idiom? [green]", end="")
        positive = input()
        if positive:
            i.family_compound = positive
            i.family_idioms = positive
        return False

    elif fc_choice == "3":
        db_session.commit()
        return True


def test_for_missing_negs(db_session, fc_set: set):
    """
    Find words with missing family_compounds and idiom.
    """
    db = db_session.query(DpdHeadword).all()
    db: list[DpdHeadword]
    total_counter = 0
    counter = 0
    for pass_no in range(3):
        should_break = False
        for i in db:
            if (
                i.meaning_1
                and not i.family_compound
                and i.neg
                and i.pos not in ["sandhi", "idiom"]
                and i.id not in neg_exceptions
            ):
                if pass_no == 0:
                    total_counter += 1

                elif pass_no in [1, 2]:
                    positive = make_positive(i)

                    # handle existing family compounds first
                    if (pass_no == 1 and positive and positive in fc_set) or (
                        pass_no == 2 and positive not in fc_set
                    ):
                        counter += 1
                        should_break = router(
                            counter, total_counter, i, positive, fc_set, db_session
                        )
                        if should_break:
                            break
        if should_break:
            break


def main():
    p_title("Add missing family compounds to negative words")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    fc_set = make_family_compound_and_idiom_set(db_session)
    test_for_missing_negs(db_session, fc_set)


if __name__ == "__main__":
    main()
