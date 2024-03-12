"""Database functions related to the GUI."""

import re

from rich import print
from sqlalchemy import or_
from typing import Optional, Tuple

from db.models import SBS, DpdHeadwords, DpdRoots, InflectionTemplates, Russian
from functions_daily_record import daily_record_update

from tools.i2html import make_html
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths


dpd_values_list = [
    "id", "lemma_1", "lemma_2", "pos", "grammar", "derived_from",
    "neg", "verb", "trans", "plus_case", "meaning_1", "meaning_lit",
    "meaning_2", "non_ia", "sanskrit", "root_key", "root_sign", "root_base",
    "family_root", "family_word", "family_compound", "family_idioms", "family_set",
    "construction", "derivative", "suffix", "phonetic", "compound_type",
    "compound_construction", "non_root_in_comps", "source_1", "sutta_1",
    "example_1", "source_2", "sutta_2", "example_2", "antonym", "synonym",
    "variant", "commentary", "notes", "cognate", "link", "origin", "stem",
    "pattern", "created_at", "updated_at"]


class Word:
    def __init__(
        self, lemma_1, lemma_2, pos, grammar, derived_from, neg, verb, trans,
        plus_case, meaning_1, meaning_lit, meaning_2, non_ia, sanskrit,
        root_key, root_sign, root_base, family_root, family_word,
        family_compound, family_set, construction, derivative, suffix,
        phonetic, compound_type, compound_construction, non_root_in_comps,
        source_1, sutta_1, example_1, source_2, sutta_2, example_2, antonym,
        synonym, variant, commentary, notes, cognate, link, origin, stem,
            pattern):
        self.lemma_1: str
        self.lemma_2: str
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


def print_pos_list(db_session):
    pos_db = db_session.query(
        DpdHeadwords.pos
    ).group_by(
        DpdHeadwords.pos
    ).all()
    pos_list = sorted([i.pos for i in pos_db])
    print(pos_list, end=" ")


def get_next_ids(db_session, window):

    used_ids = db_session.query(DpdHeadwords.id).order_by(DpdHeadwords.id).all()

    def find_missing_or_next_id():
        counter = 1
        for used_id in used_ids:
            if counter != int(used_id.id):
                return counter
            else:
                counter += 1
        return counter

    next_id = find_missing_or_next_id()
    print(next_id)

    window["id"].update(next_id)


def values_to_pali_word(values):
    word_to_add = DpdHeadwords()
    for attr in word_to_add.__table__.columns.keys():
        if attr in values:
            setattr(word_to_add, attr, values[attr])
    print(word_to_add)
    return word_to_add


def udpate_word_in_db(
        pth: ProjectPaths,
        db_session,
        window,
        values: dict
) -> Tuple[bool, str]:
    
    word_to_add = values_to_pali_word(values)
    word_id = values["id"]
    pali_word_in_db = db_session.query(DpdHeadwords).filter(
        values["id"] == DpdHeadwords.id).first()

    # add if word not in db
    if not pali_word_in_db:
        try:
            db_session.add(word_to_add)
            db_session.commit()
            window["messages"].update(
                f"'{values['lemma_1']}' added to db",
                text_color="white")
            daily_record_update(window, pth, "add", word_id)
            make_html(pth, [values["lemma_1"]])
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
                f"'{values['lemma_1']}' updated in db",
                text_color="white")
            daily_record_update(window, pth, "edit", word_id)
            make_html(pth, [values["lemma_1"]])
            return True, "updated"

        except Exception as e:
            window["messages"].update(
                f"{str(e)}", text_color="red")
            db_session.rollback()
            return False, "updated"


def edit_word_in_db(db_session, values, window):
    pali_word = fetch_id_or_lemma_1(
        db_session, values, "word_to_clone_edit")

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
        window["search_for"].update(pali_word.lemma_clean[:-1])

    return pali_word


def copy_word_from_db(db_session, values, window):

    pali_word = fetch_id_or_lemma_1(
        db_session, values, "word_to_clone_edit")

    if pali_word is None:
        message = f"{values['word_to_clone_edit']}' not found in db"
        window["messages"].update(message, text_color="red")

    else:
        exceptions = [
            "id", "lemma_1", "lemma_2",
            "antonym", "synonym", "variant", 
            "source_1", "sutta_1", "example_1",
            "source_2", "sutta_2", "example_2",
            "commentary", "meaning_2",
            "origin",
        ]

        attrs = pali_word.__dict__
        for key in attrs.keys():
            if (
                key in values
                and key not in exceptions
                and not values[key] 
            ):
                window[key].update(attrs[key])
        window["messages"].update(
            f"copied '{values['word_to_clone_edit']}'", text_color="white")


def get_verb_values(db_session):
    results = db_session.query(
        DpdHeadwords.verb
    ).group_by(
        DpdHeadwords.verb
    ).all()
    verb_values = sorted([v[0] for v in results])
    return verb_values

# get_verb_values()


def get_case_values(db_session):
    results = db_session.query(
        DpdHeadwords.plus_case
    ).group_by(
        DpdHeadwords.plus_case
    ).all()
    case_values = sorted([v[0] for v in results])
    return case_values


# get_case_values()

def get_root_key_values(db_session):
    results = db_session.query(
        DpdHeadwords.root_key
    ).group_by(
        DpdHeadwords.root_key
    ).all()
    root_key_values = sorted([v[0] for v in results if v[0] is not None])
    return root_key_values


# get_root_key_values()

def get_family_root_values(db_session, root_key):
    results = db_session.query(
        DpdRoots
    ).filter(
        DpdRoots.root == root_key
    ).first()
    if results is not None:
        family_root_values = results.root_family_list
        return family_root_values
    else:
        return []


# get_family_root_values("√kar")

def get_root_sign_values(db_session, root_key):
    results = db_session.query(
        DpdHeadwords.root_sign
    ).filter(
        DpdHeadwords.root_key == root_key
    ).group_by(
        DpdHeadwords.root_sign
    ).all()
    root_sign_values = sorted([v[0] for v in results])
    return root_sign_values


# get_root_sign_values("√kar")

def get_root_base_values(db_session, root_key):
    results = db_session.query(
        DpdHeadwords.root_base
    ).filter(
        DpdHeadwords.root_key == root_key
    ).group_by(
        DpdHeadwords.root_base
    ).all()
    root_base_values = sorted([v[0] for v in results])
    return root_base_values


# print(get_root_base_values("√heṭh"))


def get_family_word_values(db_session):
    results = db_session.query(
        DpdHeadwords.family_word
    ).group_by(
        DpdHeadwords.family_word
    ).all()
    family_word_values = sorted([v[0] for v in results if v[0] is not None])
    return family_word_values


# print(get_family_word_values())


def get_family_compound_values(db_session):
    results = db_session.query(DpdHeadwords).all()
    family_compound_values = []
    for i in results:
        family_compound_values.extend(i.family_compound_list)

    family_compound_values = sorted(
        set(family_compound_values), key=pali_sort_key)
    return family_compound_values


def get_family_idioms_values(db_session):
    results = db_session.query(DpdHeadwords).all()
    family_idioms_values = []
    for i in results:
        i: DpdHeadwords
        family_idioms_values.extend(i.family_idioms_list)

    family_idioms_values = sorted(
        set(family_idioms_values), key=pali_sort_key)
    return family_idioms_values


# print(get_family_compound_values())


def get_derivative_values(db_session):
    results = db_session.query(
        DpdHeadwords.derivative
    ).group_by(
        DpdHeadwords.derivative
    ).all()
    derivative_values = sorted([v[0] for v in results])
    return derivative_values


# print(get_derivative_values())


def get_compound_type_values(db_session):
    results = db_session.query(
        DpdHeadwords.compound_type
    ).group_by(
        DpdHeadwords.compound_type
    ).all()
    compound_type_values = sorted([v[0] for v in results])
    return compound_type_values


# print(get_compound_type_values())

def get_synonyms(
        db_session, pos: str, string_of_meanings: str, lemma_1: str) -> str:
    
    # remove brackets and split on semicolons
    string_of_meanings = re.sub(r" \(.*?\)|\(.*?\) ", "", string_of_meanings)
    list_of_meanings = string_of_meanings.split("; ")

    # remove the number from lemma_1
    lemma_1_clean = re.sub(r" \d.*$", "", lemma_1)

    # search for similar meanings
    results = db_session.query(
        DpdHeadwords
        ).filter(
            DpdHeadwords.pos == pos,
            or_(*[DpdHeadwords.meaning_1.like(
                f"%{meaning}%") for meaning in list_of_meanings])
        ).all()

    # make a dictioanary of all meanings
    meaning_dict = {}
    for i in results:
        if i.meaning_1:  # check if it's not None and not an empty string
            for meaning in i.meaning_1.split("; "):
                meaning_clean = re.sub(r" \(.*?\)|\(.*?\) ", "", meaning)
                if meaning_clean in list_of_meanings:
                    if meaning_clean not in meaning_dict:
                        meaning_dict[meaning_clean] = set([i.lemma_clean])
                    else:
                        meaning_dict[meaning_clean].add(i.lemma_clean)

    # test if two meanings are the same
    synonyms_set = set()
    for key_1 in meaning_dict:
        for key_2 in meaning_dict:
            if key_1 != key_2:
                intersection = meaning_dict[key_1].intersection(
                    meaning_dict[key_2])
                synonyms_set.update(intersection)
    
    # remove the word itself
    synonyms_set.discard(lemma_1_clean)
    
    # join into a comma seperated string
    synonyms_string = ", ".join(sorted(synonyms_set, key=pali_sort_key))
    print(synonyms_string)

    return synonyms_string


# print(get_synonyms_and_variants("fem", "talk; speech; statement"))


def get_sanskrit(db_session, construction: str) -> str:
    constr_splits = construction.split(" + ")
    sanskrit = ""
    already_added = []
    for constr_split in constr_splits:
        results = db_session.query(DpdHeadwords)\
            .filter(DpdHeadwords.lemma_1.like(f"%{constr_split}%"))\
            .all()
        for i in results:
            if i.lemma_clean == constr_split:
                if i.sanskrit not in already_added:
                    if constr_split != constr_splits[-1]:
                        sanskrit += f"{i.sanskrit} + "
                    else:
                        sanskrit += f"{i.sanskrit} "
                    already_added += [i.sanskrit]
    
    sanskrit = re.sub(r"\[.*?\]", "", sanskrit) # remove square brackets
    sanskrit = re.sub("  ", " ", sanskrit)  # remove double spaces
    sanskrit = sanskrit.replace("+ +", "+") # remove double plus signs    
    sanskrit = sanskrit.strip()

    return sanskrit


# print(get_sanskrit("sāvaka + saṅgha + ika"))

def get_patterns(db_session):
    results = db_session.query(
        InflectionTemplates.pattern
    ).all()
    inflection_patterns = sorted([v[0] for v in results])
    return inflection_patterns

# print(get_patterns())


def get_family_set_values(db_session):
    results = db_session.query(
        DpdHeadwords.family_set
    ).all()

    family_sets = []
    for r in results:
        if r.family_set is not None:
            sets = r.family_set.split("; ")
            family_sets += [set for set in sets]
    return sorted(set(family_sets))


# print(get_family_set_values())


def make_all_inflections_set(db_session):

    inflections_db = db_session.query(DpdHeadwords).all()

    all_inflections_set = set()
    for i in inflections_db:
        all_inflections_set.update(i.inflections_list)

    print(f"all_inflections_set: {len(all_inflections_set)}")
    return all_inflections_set


def get_lemma_clean_list(db_session):
    results = db_session.query(DpdHeadwords).all()
    return [i.lemma_clean for i in results]


def delete_word(pth, db_session, values, window):
    try:
        word_id = values["id"]
        db_session.query(DpdHeadwords).filter(word_id == DpdHeadwords.id).delete()
        db_session.commit()
        
        # also delete from Russian and SBS tables
        try:
            db_session.query(Russian).filter(word_id == Russian.id).delete()
        except Exception:
            print("[red]no Russian word found")
        try:
            db_session.query(SBS).filter(word_id == SBS.id).delete()
        except Exception:
            print("[red]no SBS word found")

        db_session.commit()
        daily_record_update(window, pth, "delete", word_id)
        return True
    except Exception as e:
        window["messages"].update(e, text_color="red")
        return False


def get_root_info(db_session, root_key):
    r = db_session.query(
        DpdRoots).filter(
            DpdRoots.root == root_key
        ).first()

    if r:
        root_info = f"{r.root_clean} {r.root_group} "
        root_info += f"{r.root_sign} ({r.root_meaning})"
        return root_info
    else:
        print("No matching DpdRoots found for given root_key.")
        return None


# print(get_root_info("√kar"))

def remove_line_breaker(word):
    """Remove a line breaker from the end of the word if it exists."""
    if word.endswith('\n'):
        return word[:-1]
    else:
        return word


def fetch_id_or_lemma_1(db_session, values: dict, field: str) -> Optional[DpdHeadwords]:
    """Get id or pali1 from db."""
    id_or_lemma_1 = values[field]

    id_or_lemma_1 = remove_line_breaker(id_or_lemma_1) 

    if not id_or_lemma_1:  # Check if id_or_lemma_1 is empty
        return None
        
    first_character = id_or_lemma_1[0]
    if first_character.isalpha():
        query = db_session.query(DpdHeadwords).filter(
            DpdHeadwords.lemma_1 == id_or_lemma_1).first()
        if query:
            return query
    elif first_character.isdigit():
        query = db_session.query(DpdHeadwords).filter(
            DpdHeadwords.id == id_or_lemma_1).first()
        if query:
            return query


def del_syns_if_pos_meaning_changed(
        db_session,
        values: dict,
        pali_word_original2: Optional[DpdHeadwords]
):
        """Delete all occurences of the headword 
        in the synonms column of the db if
        - the pos has changed
        - meaning_1 has changed."""
        
        if pali_word_original2:
            if (    
                pali_word_original2.pos != values["pos"]
                or pali_word_original2.meaning_1 != values["meaning_1"]
            ):
                lemma_clean = re.sub(" \\d.*$", "", values["lemma_1"])
                search_term = f"(, |^){lemma_clean}(, |$)"

                results = db_session \
                    .query(DpdHeadwords) \
                    .filter(DpdHeadwords.synonym.regexp_match(search_term)) \
                    .all()

                for r in results:
                    r.synonym = re.sub(search_term, "", r.synonym)
                    print(f"[green]deleted synonym [white]{lemma_clean}[/white] from [white]{r.lemma_1}")

                db_session.commit()
                print("[green]db_session committed ")