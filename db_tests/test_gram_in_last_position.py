#!/usr/bin/env python3

"""Test that grammatical terms always come in the last position."""

import re
import pyperclip
from rich import print

from sqlalchemy import or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_title, p_yes


class GlobalVars():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    i: DpdHeadword

    contains_grammar_set: set[str] = set()
    truncated_lemma: str
    fix_me_list: list[str] = []
    fix_me_total: int = 0
    fix_me_count: int = 0



def find_all_lemma_with_gram(g: GlobalVars):
    """Make a set of all lemma_1 (minus the last digit) which contains (gram)."""

    p_green("finding all lemmas with (gram)")

    contains_grammar = g.db_session.query(DpdHeadword) \
    .filter(
        or_(
            DpdHeadword.meaning_1.regexp_match(r"^\(gram\)"),
            DpdHeadword.meaning_2.regexp_match(r"^\(gram\)")
            )) \
    .filter(DpdHeadword.lemma_1.regexp_match(r"\d")) \
    .order_by(DpdHeadword.lemma_1) \
    .all()

    for i in contains_grammar:
        truncated_lemma = re.sub(r"\d*$", "", i.lemma_1)
        g.contains_grammar_set.add(truncated_lemma)

    p_yes(len(g.contains_grammar_set))


def test_last_position(g: GlobalVars):
    """Find (gram) not in last position."""

    p_green("finding (gram) not in last position")
    for g.truncated_lemma in g.contains_grammar_set:

        headwords = g.db_session.query(DpdHeadword) \
            .filter(DpdHeadword.lemma_1.regexp_match(fr"^{g.truncated_lemma}\d*$")) \
            .order_by(DpdHeadword.lemma_1.desc()) \
            .all()
        
        current_contains_gram = None
        previous_contains_gram = None
        
        for count, i in enumerate(headwords):
            
            previous_contains_gram = current_contains_gram

            if "(gram)" in i.meaning_combo:    
                current_contains_gram = True
            else:
                current_contains_gram = False
            
            if previous_contains_gram is False and current_contains_gram is True:
                g.fix_me_list.append(g.truncated_lemma)      
                g.fix_me_total += 1
        
    p_yes(len(g.fix_me_list))

    p_green_title(f"found {g.fix_me_total} words with (gram) not in last position.")


def reorder_grammar(g: GlobalVars):
    """Automatically reorder the words with (gram) to the end."""

    p_green_title("automatically reorder grammar")
    
    for g.truncated_lemma in g.fix_me_list:

        g.fix_me_count += 1

        print()
        print(f"{g.fix_me_count:>4} / ", end="")
        print(f"{g.fix_me_total:<4}", end="")
        print(f"{g.truncated_lemma}")
        print()

        headwords = g.db_session.query(DpdHeadword) \
            .filter(DpdHeadword.lemma_1.regexp_match(fr"^{g.truncated_lemma}\d*$")) \
            .order_by(DpdHeadword.lemma_1.asc()) \
            .all()

        digits = []
        for h in headwords:
            last_digits = re.sub(g.truncated_lemma, "", h.lemma_1)
            digits.append(int(last_digits))
            print(h.lemma_1, h.meaning_combo)
        
        print()
        digits = sorted(digits)

        if max(digits) < 10:
        
            # reorder with 'x' in last position to avoid unique constraint errors 
            for h in headwords:
                if "(gram)" in h.meaning_combo:
                    h.lemma_1 = f"{g.truncated_lemma}{digits[-1]}x"
                    del(digits[-1])
                else:
                    h.lemma_1 = f"{g.truncated_lemma}{digits[0]}x"
                    del(digits[0])
            
            g.db_session.commit()

            # remove 'x' in last place
            for h in headwords:
                h.lemma_1 = re.sub("x$", "", h.lemma_1)
                print(h.lemma_1, h.meaning_combo)
            
            g.db_session.commit()

        else:
            print("please re-order manually")

        print()
        print("press any key to continue... ", end="")
        pyperclip.copy(f"/^{g.truncated_lemma}/")
        input()



def main():
    p_title("test for (gram) not in last position")
    g = GlobalVars()
    find_all_lemma_with_gram(g)
    test_last_position(g)
    if g.fix_me_total > 0:
        reorder_grammar(g)
        

if __name__ == "__main__":
    main()