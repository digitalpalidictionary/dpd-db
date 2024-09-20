#!/usr/bin/env python3

"""Find words in example_1, example_2 and commentary columns which
level 1. doesn't exist in the lookup table
level 2. needs meaning and above
level 3. needs example and above
"""

import re

from rich import print
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths
from tools.clean_machine import clean_machine

class GlobalVars():
    def __init__(self, db_session: Session, text: str, level=1) -> None:
        self.db_session: Session = db_session
        self.text: str = text
        self.missing_meanings: list[str] = []
        self.text_list: list[str]
        self.word: str
        self.lookup: Lookup | None
        self.level: int = level
    
    def append_to_text_list(self, word):
        if word not in self.text_list:
            self.text_list.append(word)


def make_clean_word_list(g: GlobalVars):
    """Clean up the text and make a list of words."""

    g.text = re.sub("\(.*?\)", "", g.text)      # remove word in brackets
    g.text = g.text.replace("<b>", "")            # remove bold tags
    g.text = g.text.replace("</b>", "")     
    g.text = clean_machine(g.text)
    g.text_list = sorted(set(g.text.split()))


def check_in_lookup(g: GlobalVars):
    g.lookup = g.db_session.query(Lookup) \
        .filter_by(lookup_key=g.word) \
        .first()


def check_in_dpd_headwords(g: GlobalVars):

    for dpd_id in g.lookup.headwords_unpack:
        headword = g.db_session.query(DpdHeadword) \
            .filter_by(id=dpd_id) \
            .first()
        if g.level == 2:
            if not headword.meaning_1:
                g.missing_meanings.append(headword.lemma_1)
        if g.level == 3:
            if not headword.example_1:
                g.missing_meanings.append(headword.lemma_1)


def check_in_deconstructor(g: GlobalVars):
    """"""
    for deconstruction in g.lookup.deconstructor_unpack:
        deconstruction = re.sub(r" \[.+", "", deconstruction)
        for word in deconstruction.split(" + "):
            g.append_to_text_list(word)


def find_missing_meanings(db_session: Session, text: str, level: int = 1):
    """Take a sentence
    1. clean it up, remove all punctuation
    2. split into words
    3. find if those words have meaning_1 or example_1

    level 1: find all words not recognized
    level 2: find all words with missing meaning_1 (and level 1)
    level 3: find all words with missing example_2 (and level 1 and 2)
    """
    g = GlobalVars(db_session, text, level=1)
    make_clean_word_list(g)

    for g.word in g.text_list:
        check_in_lookup(g)
        if g.lookup:
            if g.lookup.headwords:
                check_in_dpd_headwords(g)
            if g.lookup.deconstructor:
                check_in_deconstructor(g)
        else:
            g.missing_meanings.append(g.word)

    g.missing_meanings = sorted(set(g.missing_meanings))
    print(g.missing_meanings)
    return g.missing_meanings


if __name__ == "__main__":
    text = """
    362. atha kho sīho samaṇuddeso yenāyasmā nāgito tenupasaṅkami, kuppinti upasaṅkamitvā āyasmantaṃ nāgitaṃ abhivādetvā ekamantaṃ aṭṭhāsi. ekamantaṃ ṭhito kho sīho samaṇuddeso āyasmantaṃ nāgitaṃ etadavoca – "ete, bhante kassapa, sambahulā kosalakā ca brāhmaṇadūtā māgadhakā ca brāhmaṇadūtā idhūpasaṅkantā bhagavantaṃ dassanāya, oṭṭhaddhopi licchavī mahatiyā licchavīparisāya saddhiṃ idhūpasaṅkanto bhagavantaṃ dassanāya, sādhu, bhante kassapa, labhataṃ esā janatā bhagavantaṃ dassanāyā"ti.
    """
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    missing_meanings = find_missing_meanings(db_session, text, level=1)
    # print(missing_meanings)
    


