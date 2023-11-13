"""Database functions related to the GUI."""

import re

from rich import print
from sqlalchemy import or_
from typing import Optional, Tuple

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot, InflectionTemplates, DerivedData
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths

PTH = ProjectPaths()
db_session = get_db_session(PTH.dpd_db_path)

dpd_values_list = [
    "id", "user_id", "pali_1", "pali_2", "pos", "grammar", "derived_from",
    "neg", "verb", "trans", "plus_case", "meaning_1", "meaning_lit",
    "meaning_2", "non_ia", "sanskrit", "root_key", "root_sign", "root_base",
    "family_root", "family_word", "family_compound", "family_set",
    "construction", "derivative", "suffix", "phonetic", "compound_type",
    "compound_construction", "non_root_in_comps", "source_1", "sutta_1",
    "example_1", "source_2", "sutta_2", "example_2", "antonym", "synonym",
    "variant", "commentary", "notes", "cognate", "link", "origin", "stem",
    "pattern", "created_at", "updated_at"]


class Word:
    def __init__(
        self, pali_1, pali_2, pos, grammar, derived_from, neg, verb, trans,
        plus_case, meaning_1, meaning_lit, meaning_2, non_ia, sanskrit,
        root_key, root_sign, root_base, family_root, family_word,
        family_compound, family_set, construction, derivative, suffix,
        phonetic, compound_type, compound_construction, non_root_in_comps,
        source_1, sutta_1, example_1, source_2, sutta_2, example_2, antonym,
        synonym, variant, commentary, notes, cognate, link, origin, stem,
            pattern):
        self.pali_1: str
        self.pali_2: str
        self.pos: str
        self.grammar: str
        self.derived_from: str
        self.neg: str
        self.verb: str
        self.trans: str
        self.plus_case: str
        self.meaning_1: str
        self.meaning_lit: str
        self.meaning_2: str
        self.non_ia: str
        self.sanskrit: str
        self.root_key: str
        self.root_sign: str
        self.root_base: str
        self.family_root: str
        self.family_word: str
        self.family_compound: str
        self.family_set: str
        self.construction: str
        self.derivative: str
        self.suffix: str
        self.phonetic: str
        self.compound_type: str
        self.compound_construction: str
        self.non_root_in_comps: str
        self.source_1: str
        self.sutta_1: str
        self.example_1: str
        self.source_2: str
        self.sutta_2: str
        self.example_2: str
        self.antonym: str
        self.synonym: str
        self.variant: str
        self.commentary: str
        self.notes: str
        self.cognate: str
        self.link: str
        self.origin: str
        self.stem: str
        self.pattern: str


def print_pos_list():
    pos_db = db_session.query(
        PaliWord.pos
    ).group_by(
        PaliWord.pos
    ).all()
    pos_list = sorted([i.pos for i in pos_db])
    print(pos_list, end=" ")


def get_next_ids(window):

    used_ids = db_session.query(PaliWord.id).order_by(PaliWord.id).all()
    used_uids = db_session.query(PaliWord.user_id).order_by(
        PaliWord.user_id).all()

    def find_missing_or_next_id():
        counter = 1
        for used_id in used_ids:
            if counter != int(used_id.id):
                return counter
            else:
                counter += 1
        return counter

    def find_missing_or_next_user_id():
        counter = 1
        for uid in used_uids:
            if counter != int(uid.user_id):
                return counter
            else:
                counter += 1
        return counter

    next_id = find_missing_or_next_id()
    next_uid = find_missing_or_next_user_id()
    print(next_id, next_uid)

    window["id"].update(next_id)
    window["user_id"].update(next_uid)


def values_to_pali_word(values):
    word_to_add = PaliWord()
    for attr in word_to_add.__table__.columns.keys():
        if attr in values:
            setattr(word_to_add, attr, values[attr])
    print(word_to_add)
    return word_to_add


def udpate_word_in_db(
        window, values: dict) -> Tuple[bool, str]:
    word_to_add = values_to_pali_word(values)
    pali_word_in_db = db_session.query(PaliWord).filter(
        values["id"] == PaliWord.id).first()

    # add if word not in db
    if not pali_word_in_db:
        try:
            db_session.add(word_to_add)
            db_session.commit()
            window["messages"].update(
                f"'{values['pali_1']}' added to db",
                text_color="white")
            return True, "added"

        except Exception as e:
            window["messages"].update(f"{str(e)}", text_color="red")
            db_session.rollback()
            return False, "added"

    # update if word in db
    else:
        for value in values:
            if value in dpd_values_list:
                setattr(pali_word_in_db, value, values[value])

        try:
            db_session.commit()
            window["messages"].update(
                f"'{values['pali_1']}' updated in db",
                text_color="white")
            return True, "updated"

        except Exception as e:
            window["messages"].update(
                f"{str(e)}", text_color="red")
            db_session.rollback()
            return False, "updated"


def edit_word_in_db(values, window):
    pali_word = fetch_id_or_pali_1(
        values, "word_to_clone_edit")

    if pali_word is None:
        message = f"{values['word_to_clone_edit']}' not found in db"
        window["messages"].update(message, text_color="red")

    else:
        attrs = pali_word.__dict__
        for key in attrs.keys():
            if key in values:
                window[key].update(attrs[key])
        window["messages"].update(
            f"editing '{values['word_to_clone_edit']}'", text_color="white")

    return pali_word


def copy_word_from_db(values, window):

    pali_word = fetch_id_or_pali_1(
        values, "word_to_clone_edit")

    if pali_word is None:
        message = f"{values['word_to_clone_edit']}' not found in db"
        window["messages"].update(message, text_color="red")

    else:
        exceptions = [
            "id", "user_id", "pali_1", "pali_2", "origin", "source_1",
            "sutta_1", "example_1", "source_2", "sutta_2", "example_2",
            "commentary", "meaning_2"
        ]

        attrs = pali_word.__dict__
        for key in attrs.keys():
            if key in values:
                if key not in exceptions:
                    window[key].update(attrs[key])
        window["messages"].update(
            f"copied '{values['word_to_clone_edit']}'", text_color="white")


def get_verb_values():
    results = db_session.query(
        PaliWord.verb
    ).group_by(
        PaliWord.verb
    ).all()
    verb_values = sorted([v[0] for v in results])
    return verb_values

# get_verb_values()


def get_case_values():
    results = db_session.query(
        PaliWord.plus_case
    ).group_by(
        PaliWord.plus_case
    ).all()
    case_values = sorted([v[0] for v in results])
    return case_values


# get_case_values()

def get_root_key_values():
    results = db_session.query(
        PaliWord.root_key
    ).group_by(
        PaliWord.root_key
    ).all()
    root_key_values = sorted([v[0] for v in results if v[0] is not None])
    return root_key_values


# get_root_key_values()

def get_family_root_values(root_key):
    results = db_session.query(
        PaliRoot
    ).filter(
        PaliRoot.root == root_key
    ).first()
    if results is not None:
        family_root_values = results.root_family_list
        return family_root_values
    else:
        return []


# get_family_root_values("√kar")

def get_root_sign_values(root_key):
    results = db_session.query(
        PaliWord.root_sign
    ).filter(
        PaliWord.root_key == root_key
    ).group_by(
        PaliWord.root_sign
    ).all()
    root_sign_values = sorted([v[0] for v in results])
    return root_sign_values


# get_root_sign_values("√kar")

def get_root_base_values(root_key):
    results = db_session.query(
        PaliWord.root_base
    ).filter(
        PaliWord.root_key == root_key
    ).group_by(
        PaliWord.root_base
    ).all()
    root_base_values = sorted([v[0] for v in results])
    return root_base_values


# print(get_root_base_values("√heṭh"))


def get_family_word_values():
    results = db_session.query(
        PaliWord.family_word
    ).group_by(
        PaliWord.family_word
    ).all()
    family_word_values = sorted([v[0] for v in results if v[0] is not None])
    return family_word_values


# print(get_family_word_values())


def get_family_compound_values():
    results = db_session.query(PaliWord).all()
    family_compound_values = []
    for i in results:
        family_compound_values.extend(i.family_compound_key_list)

    family_compound_values = sorted(
        set(family_compound_values), key=pali_sort_key)
    return family_compound_values


# print(get_family_compound_values())


def get_derivative_values():
    results = db_session.query(
        PaliWord.derivative
    ).group_by(
        PaliWord.derivative
    ).all()
    derivative_values = sorted([v[0] for v in results])
    return derivative_values


# print(get_derivative_values())


def get_compound_type_values():
    results = db_session.query(
        PaliWord.compound_type
    ).group_by(
        PaliWord.compound_type
    ).all()
    compound_type_values = sorted([v[0] for v in results])
    return compound_type_values


# print(get_compound_type_values())

def get_synonyms(pos: str, string_of_meanings: str) -> str:

    string_of_meanings = re.sub(r" \(.*?\)|\(.*?\) ", "", string_of_meanings)
    list_of_meanings = string_of_meanings.split("; ")

    results = db_session.query(
        PaliWord
        ).filter(
            PaliWord.pos == pos,
            or_(*[PaliWord.meaning_1.like(
                f"%{meaning}%") for meaning in list_of_meanings])
        ).all()

    meaning_dict = {}
    for i in results:
        if i.meaning_1:  # check if it's not None and not an empty string
            for meaning in i.meaning_1.split("; "):
                meaning_clean = re.sub(r" \(.*?\)|\(.*?\) ", "", meaning)
                if meaning_clean in list_of_meanings:
                    if meaning_clean not in meaning_dict:
                        meaning_dict[meaning_clean] = set([i.pali_clean])
                    else:
                        meaning_dict[meaning_clean].add(i.pali_clean)

    synonyms = set()
    for key_1 in meaning_dict:
        for key_2 in meaning_dict:
            if key_1 != key_2:
                intersection = meaning_dict[key_1].intersection(
                    meaning_dict[key_2])
                synonyms.update(intersection)
    synonyms = ", ".join(sorted(synonyms, key=pali_sort_key))
    print(synonyms)
    return synonyms


# print(get_synonyms_and_variants("fem", "talk; speech; statement"))


def get_sanskrit(construction: str) -> str:
    constr_splits = construction.split(" + ")
    sanskrit = ""
    already_added = []
    for constr_split in constr_splits:
        results = db_session.query(
            PaliWord
            ).filter(
                PaliWord.pali_1.like(f"%{constr_split}%")
            ).all()
        for i in results:
            if i.pali_clean == constr_split:
                if i.sanskrit not in already_added:
                    if constr_split != constr_splits[-1]:
                        sanskrit += f"{i.sanskrit} + "
                    else:
                        sanskrit += f"{i.sanskrit} "
                    already_added += [i.sanskrit]

    return sanskrit


# print(get_sanskrit("sāvaka + saṅgha + ika"))

def get_patterns():
    results = db_session.query(
        InflectionTemplates.pattern
    ).all()
    inflection_patterns = sorted([v[0] for v in results])
    return inflection_patterns

# print(get_patterns())


def get_family_set_values():
    results = db_session.query(
        PaliWord.family_set
    ).all()

    family_sets = []
    for r in results:
        if r.family_set is not None:
            sets = r.family_set.split("; ")
            family_sets += [set for set in sets]
    return sorted(set(family_sets))


# print(get_family_set_values())


def make_all_inflections_set():

    inflections_db = db_session.query(DerivedData).all()

    all_inflections_set = set()
    for i in inflections_db:
        all_inflections_set.update(i.inflections_list)

    print(f"all_inflections_set: {len(all_inflections_set)}")
    return all_inflections_set


def get_pali_clean_list():
    results = db_session.query(PaliWord).all()
    return [i.pali_clean for i in results]


def delete_word(values, window):
    try:
        row_id = values["id"]
        db_session.query(PaliWord).filter(row_id == PaliWord.id).delete()
        db_session.commit()
        return True
    except Exception as e:
        window["messages"].update(e, text_color="red")
        return False


def get_root_info(root_key):
    r = db_session.query(
        PaliRoot).filter(
            PaliRoot.root == root_key
        ).first()

    if r:
        root_info = f"{r.root_clean} {r.root_group} "
        root_info += f"{r.root_sign} ({r.root_meaning})"
        return root_info
    else:
        print("No matching PaliRoot found for given root_key.")
        return None


# print(get_root_info("√kar"))

def remove_line_breaker(word):
    """Remove a line breaker from the end of the word if it exists."""
    if word.endswith('\n'):
        return word[:-1]
    else:
        return word


def fetch_id_or_pali_1(values: dict, field: str) -> Optional[PaliWord]:
    """Get id or pali1 from db."""
    id_or_pali_1 = values[field]

    id_or_pali_1 = remove_line_breaker(id_or_pali_1) 

    if not id_or_pali_1:  # Check if id_or_pali_1 is empty
        return None
        
    first_character = id_or_pali_1[0]
    if first_character.isalpha():
        query = db_session.query(PaliWord).filter(
            PaliWord.pali_1 == id_or_pali_1).first()
        if query:
            return query
    elif first_character.isdigit():
        query = db_session.query(PaliWord).filter(
            PaliWord.id == id_or_pali_1).first()
        if query:
            return query

