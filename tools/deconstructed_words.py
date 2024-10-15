"""Compiles lists of all deconstructed compounds in db's Lookup table,
or individual words in splits."""

from sqlalchemy.orm import Session
from db.models import Lookup


def make_deconstructor_words_set(db_session: Session) -> set:
    """Input a db_session.
    Returns a list of all deconstructed compounds in their raw form."""

    results = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
    return set([r.deconstructor for r in results])


def make_words_in_deconstructions(db_session: Session) -> set:
    """Input a db_sesion.
    Returns a list of all words in deconstructed compound splits."""

    results = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()

    deconstructed_words = set()
    for i in results:
        deconstructions = i.deconstructor_unpack
        for deconstruction in deconstructions:
            for word in deconstruction.split(" + "):
                deconstructed_words.add(word)
    return deconstructed_words
