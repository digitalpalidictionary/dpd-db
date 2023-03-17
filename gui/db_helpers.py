import re

from rich import print
from sqlalchemy import desc, or_
from json import loads


from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot, InflectionTemplates
from db.models import DerivedData
from db.db_helpers import print_column_names
from tools.pali_sort_key import pali_sort_key

print_column_names(PaliWord)

db_session = get_db_session("dpd.db")

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


def print_pos_list() -> list:
    pos_db = db_session.query(
        PaliWord.pos
    ).group_by(
        PaliWord.pos
    ).all()
    pos_list = sorted([i.pos for i in pos_db])
    return print(pos_list, end=" ")


def get_next_ids(window):
    # get next id
    last_id = db_session.query(PaliWord.id).order_by(
        desc(PaliWord.id)).first()[0]
    next_id = last_id+1

    # get next user id
    last_user_id = db_session.query(PaliWord.user_id).order_by(
        desc(PaliWord.user_id)).first()[0]
    next_user_id = last_user_id+1

    window["id"].update(next_id)
    window["user_id"].update(next_user_id)


def values_to_pali_word(values):
    word_to_add = PaliWord()
    for attr in word_to_add.__table__.columns.keys():
        if attr in values:
            setattr(word_to_add, attr, values[attr])
    print(word_to_add)
    return word_to_add


def add_word_to_db(window, values: dict) -> None:
    word_to_add = values_to_pali_word(values)

    exists = db_session.query(
        PaliWord
        ).filter(
            PaliWord.pali_1 == values["pali_1"]
        ).first()

    if exists:
        window["messages"].update(
            f"""'{values['pali_1']}' already in db. Use Update instead""",
            text_color="red")
        return False

    else:
        try:
            db_session.add(word_to_add)
            db_session.commit()
            window["messages"].update(
                f"'{values['pali_1']}' added to db",
                text_color="white")
            return True
        except Exception as e:
            window["messages"].update(
                f"{str(e)}", text_color="red")
            return False


def update_word_in_db(window, values: dict) -> None:
    # dict_to_add = [values_to_dict(values)]

    word = db_session.query(
        PaliWord
        ).filter(
            PaliWord.id == values["id"]
        ).first()

    if not word:
        window["messages"].update(
            f"""'{values['pali_1']}' not in db. Use Add to db instead""",
            text_color="red")
        return False

    else:
        for key in values:
            if key in dpd_values_list:
                setattr(word, key, values[key])

        try:
            db_session.commit()
            window["messages"].update(
                f"'{values['pali_1']}' updated in db",
                text_color="white")
            return True

        except Exception as e:
            window["messages"].update(
                f"{str(e)}", text_color="red")
            return False


def edit_word_in_db(values, window):
    pali_word = db_session.query(
        PaliWord
    ).filter(
        PaliWord.pali_1 == values["word_to_copy"]
    ).first()

    if pali_word is None:
        window["messages"].update(
            f"{values['word_to_copy']}' not found in db", text_color="red"
        ),

    else:
        attrs = pali_word.__dict__
        for key in attrs.keys():
            if key in values:
                window[key].update(attrs[key])
        window["messages"].update(
            f"editing '{values['word_to_copy']}'", text_color="white")


def copy_word_from_db(values, window):
    pali_word = db_session.query(
        PaliWord
    ).filter(
        PaliWord.pali_1 == values["word_to_copy"]
    ).first()

    if pali_word is None:
        window["messages"].update(
            "{values['word_to_copy']}' not found in db", text_color="red"
        ),

    else:
        exceptions = [
            "id", "user_id", "pali_1", "pali_2", "origin", "source_1", "sutta_1", "example_1",
            "source_2", "sutta_2", "example_2", "commentary"
        ]
        attrs = pali_word.__dict__
        for key in attrs.keys():
            if key in values:
                if key not in exceptions:
                    window[key].update(attrs[key])
        window["messages"].update(
            f"copied '{values['word_to_copy']}'", text_color="white")


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
    family_root_values = results.root_family_list
    return family_root_values


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
    family_word_values = sorted([v[0] for v in results])
    return family_word_values


# print(get_family_word_values())


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
            or_(*[PaliWord.meaning_1.like(f"%{meaning}%") for meaning in list_of_meanings])
        ).all()

    meaning_dict = {}
    for i in results:
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
                        sanskrit += f"{i.sanskrit}"
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
        sets = r.family_set.split("; ")
        family_sets += [set for set in sets]
    return sorted(set(family_sets))


# print(get_family_set_values())


def make_all_inflections_set():

    inflections_db = db_session.query(
        DerivedData.inflections
    ).all()

    all_inflections_set = set()
    for i in inflections_db:
        all_inflections_set.update(loads(i.inflections))

    print(f"all_inflections_set: {len(all_inflections_set)}")
    return all_inflections_set
