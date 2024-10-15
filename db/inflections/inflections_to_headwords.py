#!/usr/bin/env python3

"""
Save a TSV of every inflection found in texts or deconstructed compounds
and matching corresponding headwords.

Add the same data to the lookup table of the db.
"""

import csv


from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup

from tools.all_tipitaka_words import make_all_tipitaka_word_set
from tools.deconstructed_words import make_words_in_deconstructions
from tools.headwords_clean_set import make_clean_headwords_set
from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import p_green, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.update_test_add import update_test_add


class GlobalVars():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()
    all_tipitaka_word_set: set
    deconstructions_word_set: set
    clean_headwords_set: set
    all_words_set: set
    i2h_dict: dict
    i2h_dict_tpr: dict


def inflection_to_headwords(g: GlobalVars): 
    """Make a dictionary of inflections: [headwords]."""

    p_green("making inflections2headwords dict")

    g.i2h_dict = {}
    g.i2h_dict_tpr = {}

    for i in g.dpd_db:
        inflections = i.inflections_list_all # include api ca eva iti as well
        for inflection in inflections:
            if inflection in g.all_words_set:
                if inflection not in g.i2h_dict:
                    g.i2h_dict[inflection] = [i.id]
                    g.i2h_dict_tpr[inflection] = [i.lemma_1]
                elif i.id not in g.i2h_dict[inflection]:
                    g.i2h_dict[inflection].append(i.id)
                    g.i2h_dict_tpr[inflection].append(i.lemma_1)

    p_yes(len(g.i2h_dict))


def save_i2h_for_tpr(g: GlobalVars):
    """Save inflections2headwords for Tipitaka Pali Reader."""

    p_green("saving to tsv for tpr")

    with open(g.pth.tpr_i2h_tsv_path, "w") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["inflection", "headwords"])

        for inflection, headwords in g.i2h_dict_tpr.items():
            headwords = pali_list_sorter(headwords)
            headwords = ",".join(headwords)
            writer.writerow([inflection, headwords])
    
    p_yes(len(g.i2h_dict_tpr))


def add_i2h_to_db(g: GlobalVars):
    """Add inflections2headwords to the lookup table."""
    

    lookup_table = (g.db_session.query(Lookup).all())
    update_set, test_set, add_set = update_test_add(lookup_table, g.i2h_dict)

    p_green("updating db")
    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.headwords_pack(sorted(g.i2h_dict[i.lookup_key]))
        elif i.lookup_key in test_set:
            if is_another_value(i, "headwords"):
                i.headwords = ""
            else:
                g.db_session.delete(i)    
    
    g.db_session.commit()
    p_yes(len(update_set) + len(test_set))


    p_green("adding to db")
    add_to_db = []
    for inflection, ids in g.i2h_dict.items():    
        if inflection in add_set:
            add_me = Lookup()
            add_me.lookup_key = inflection
            add_me.headwords_pack(sorted(set(ids)))
            add_to_db.append(add_me)

    g.db_session.add_all(add_to_db)
    g.db_session.commit()
    g.db_session.close()
    p_yes(len(add_set))


def main():
    tic()
    p_title("inflection to headwords")

    g = GlobalVars()
    
    p_green("making all all_tipitaka_word_set")
    g.all_tipitaka_word_set = make_all_tipitaka_word_set()
    p_yes(len(g.all_tipitaka_word_set))
    
    p_green("making all deconstructed words set")
    g.deconstructions_word_set = \
        make_words_in_deconstructions(g.db_session)
    p_yes(len(g.deconstructions_word_set))

    p_green("making clean headwords set")
    g.clean_headwords_set = make_clean_headwords_set(g.dpd_db)
    p_yes(len(g.clean_headwords_set))

    p_green("making all words set")
    g.all_words_set = \
        g.all_tipitaka_word_set | g.deconstructions_word_set | g.clean_headwords_set
    p_yes(len(g.all_words_set))

    inflection_to_headwords(g)
    save_i2h_for_tpr(g)
    add_i2h_to_db(g)

    toc()


if __name__ == "__main__":
    main()
