"""Database functions related to the GUI."""

import re
import csv

from rich import print
from sqlalchemy import or_
from typing import Optional, Tuple

from db.models import SBS, DpdHeadword, DpdRoot, InflectionTemplates, Russian
from gui.functions_daily_record import daily_record_update

from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.tsv_read_write import append_tsv_list
from tools.fast_api_utils import request_dpd_server


dpd_values_list = [
    "id", "lemma_1", "lemma_2", "pos", "grammar", "derived_from",
    "neg", "verb", "trans", "plus_case", "meaning_1", "meaning_lit",
    "meaning_2", "non_ia", "sanskrit", "root_key", "root_sign", "root_base",
    "family_root", "family_word", "family_compound", "family_idioms", "family_set",
    "construction", "derivative", "suffix", "phonetic", "compound_type",
    "compound_construction", "non_root_in_comps", "source_1", "sutta_1",
    "example_1", "source_2", "sutta_2", "example_2", "antonym", "synonym",
    "variant", "commentary", "notes", "cognate", "link", "origin", "stem",
    "pattern", "created_at", "updated_at", "online_suggestion"]


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
    pos_db = db_session.query(DpdHeadword.pos).group_by(DpdHeadword.pos).all()
    pos_list = sorted([i.pos for i in pos_db])
    print(pos_list, end=" ")


def get_next_ids(db_session, window):

    db = db_session.query(DpdHeadword.id).order_by(DpdHeadword.id).all()
    max_id = max(used_id.id for used_id in db)
    next_id = max_id + 1

    window["id"].update(next_id)


def values_to_pali_word(values):
    word_to_add = DpdHeadword()
    for attr in word_to_add.__table__.columns.keys():
        if attr in values:
            setattr(word_to_add, attr, values[attr])
    print(word_to_add)
    return word_to_add


def update_word_in_db(
        pth: ProjectPaths,
        db_session,
        window,
        values: dict
) -> Tuple[bool, str]:
    
    word_to_add = values_to_pali_word(values)
    word_id = values["id"]
    pali_word_in_db = db_session.query(DpdHeadword).filter(
        values["id"] == DpdHeadword.id).first()

    # add if word not in db
    if not pali_word_in_db:
        try:
            db_session.add(word_to_add)
            db_session.commit()
            window["messages"].update(
                f"'{values['lemma_1']}' added to db",
                text_color="white")
            daily_record_update(window, pth, "add", word_id)
            request_dpd_server(values["id"])
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
            request_dpd_server(values["id"])
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
    results = db_session.query(DpdHeadword.verb).group_by(DpdHeadword.verb).all()
    verb_values = sorted([v[0] for v in results])
    return verb_values

# get_verb_values()


def get_case_values(db_session):
    results = db_session.query(DpdHeadword.plus_case).group_by(DpdHeadword.plus_case).all()
    case_values = sorted([v[0] for v in results])
    return case_values


# get_case_values()

def get_root_key_values(db_session):
    results = db_session.query(DpdHeadword.root_key).group_by(DpdHeadword.root_key).all()
    root_key_values = sorted([v[0] for v in results if v[0] is not None])
    return root_key_values


# get_root_key_values()

def get_family_root_values(db_session, root_key):
    results = db_session.query(DpdRoot).filter(DpdRoot.root == root_key).first()
    if results is not None:
        family_root_values = results.root_family_list
        return family_root_values
    else:
        return []


# get_family_root_values("√kar")

def get_root_sign_values(db_session, root_key):
    results = db_session.query(DpdHeadword.root_sign) \
        .filter(DpdHeadword.root_key == root_key) \
        .group_by(DpdHeadword.root_sign) \
        .all()
    root_sign_values = sorted([v[0] for v in results])
    return root_sign_values


# get_root_sign_values("√kar")

def get_root_base_values(db_session, root_key):
    results = db_session.query(DpdHeadword.root_base) \
        .filter(DpdHeadword.root_key == root_key) \
        .group_by(DpdHeadword.root_base) \
        .all()
    root_base_values = sorted([v[0] for v in results])
    return root_base_values


# print(get_root_base_values("√heṭh"))


def get_family_word_values(db_session):
    results = db_session.query(DpdHeadword.family_word) \
        .group_by(DpdHeadword.family_word) \
        .all()
    family_word_values = sorted([v[0] for v in results if v[0] is not None])
    return family_word_values


# print(get_family_word_values())


def get_family_compound_values(db_session):
    results = db_session.query(DpdHeadword).all()
    family_compound_values = []
    for i in results:
        family_compound_values.extend(i.family_compound_list)

    family_compound_values = sorted(
        set(family_compound_values), key=pali_sort_key)
    return family_compound_values


def get_family_idioms_values(db_session):
    results = db_session.query(DpdHeadword).all()
    family_idioms_values = []
    for i in results:
        i: DpdHeadword
        family_idioms_values.extend(i.family_idioms_list)

    family_idioms_values = sorted(
        set(family_idioms_values), key=pali_sort_key)
    return family_idioms_values


# print(get_family_compound_values())


def get_derivative_values(db_session):
    results = db_session.query(DpdHeadword.derivative) \
        .group_by(DpdHeadword.derivative) \
        .all()
    derivative_values = sorted([v[0] for v in results])
    return derivative_values


# print(get_derivative_values())


def get_compound_type_values(db_session):
    results = db_session.query(DpdHeadword.compound_type) \
        .group_by(DpdHeadword.compound_type) \
        .all()
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
    results = db_session.query(DpdHeadword) \
        .filter(
            DpdHeadword.pos == pos,
            or_(*[DpdHeadword.meaning_1.like(f"%{meaning}%") for meaning in list_of_meanings])
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
        results = db_session.query(DpdHeadword)\
            .filter(DpdHeadword.lemma_1.like(f"%{constr_split}%"))\
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
    results = db_session.query(InflectionTemplates.pattern).all()
    inflection_patterns = sorted([v[0] for v in results])
    return inflection_patterns

# print(get_patterns())


def get_family_set_values(db_session):
    results = db_session.query(DpdHeadword.family_set).all()

    family_sets = []
    for r in results:
        if r.family_set is not None:
            sets = r.family_set.split("; ")
            family_sets += [set for set in sets]
    return sorted(set(family_sets))


# print(get_family_set_values())


def make_all_inflections_set(db_session):

    inflections_db = db_session.query(DpdHeadword).all()

    all_inflections_set = set()
    for i in inflections_db:
        all_inflections_set.update(i.inflections_list)

    print(f"all_inflections_set: {len(all_inflections_set)}")
    return all_inflections_set


def get_lemma_clean_list(db_session):
    results = db_session.query(DpdHeadword).all()
    return [i.lemma_clean for i in results]


def delete_word(pth, db_session, values, window):
    try:
        word_id = values["id"]
        word_lemma = values["lemma_1"]

        db_session.query(DpdHeadword).filter(word_id == DpdHeadword.id).delete()
        db_session.commit()
        
        # also delete from Russian table
        try:
            ru_record = db_session.query(Russian).filter(word_id == Russian.id).first()
            if ru_record:
                # Save all ru to TSV
                ru_header = ["word_id", "word_lemma"]
                ru_data = [[ru_record.id, word_lemma]]
                append_tsv_list(pth.delated_words_history_pth, ru_header, ru_data)
                # Delete the Russian record
                db_session.query(Russian).filter(word_id == Russian.id).delete()
        except Exception:
            print("[red]no Russian word found")

        # also delete from SBS table
        try:
            sbs_record = db_session.query(SBS).filter(word_id == SBS.id).first()
            if sbs_record:
                # Check if any sbs_example_* fields are not empty
                sbs_examples = [sbs_record.sbs_example_1, sbs_record.sbs_example_2, sbs_record.sbs_example_3, sbs_record.sbs_example_4]
                non_empty_examples = [example for example in sbs_examples if example]
                
                if non_empty_examples:
                    # Save all non-empty sbs_example_* and id to TSV
                    sbs_header = ["word_id", "word_lemma"] + [f"sbs_example_{i+1}" for i in range(len(non_empty_examples))]
                    show_sbs_data = [[sbs_record.id, word_lemma] + non_empty_examples]
                    append_tsv_list(pth.delated_words_history_pth, sbs_header, show_sbs_data)
                    
                    # Delete the SBS record
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
    r = db_session.query(DpdRoot) \
        .filter(DpdRoot.root == root_key) \
        .first()

    if r:
        root_info = f"{r.root_clean} {r.root_group} "
        root_info += f"{r.root_sign} ({r.root_meaning})"
        return root_info
    else:
        print("No matching DpdRoot found for given root_key.")
        return None


# print(get_root_info("√kar"))

def remove_line_breaker(word):
    """Remove a line breaker from the end of the word if it exists."""
    if word.endswith('\n'):
        return word[:-1]
    else:
        return word


def fetch_id_or_lemma_1(db_session, values: dict, field: str) -> Optional[DpdHeadword]:
    """Get id or pali1 from db."""
    id_or_lemma_1 = values[field]

    id_or_lemma_1 = remove_line_breaker(id_or_lemma_1) 

    if not id_or_lemma_1:  # Check if id_or_lemma_1 is empty
        return None
        
    first_character = id_or_lemma_1[0]
    if first_character.isalpha():
        query = db_session.query(DpdHeadword).filter(
            DpdHeadword.lemma_1 == id_or_lemma_1).first()
        if query:
            return query
    elif first_character.isdigit():
        query = db_session.query(DpdHeadword).filter(
            DpdHeadword.id == id_or_lemma_1).first()
        if query:
            return query


def del_syns_if_pos_meaning_changed(
        db_session,
        values: dict,
        pali_word_original2: Optional[DpdHeadword]
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
                    .query(DpdHeadword) \
                    .filter(DpdHeadword.synonym.regexp_match(search_term)) \
                    .all()

                for r in results:
                    r.synonym = re.sub(search_term, "", r.synonym)
                    print(f"[green]deleted synonym [white]{lemma_clean}[/white] from [white]{r.lemma_1}")

                db_session.commit()
                print("[green]db_session committed ")


def make_words_to_add_list_generic(
    db_session,
    pth,
    make_cst_func,
    make_sc_func=None,
    inflection_func=make_all_inflections_set,
    book=None,
    sutta_name=None,
    dpspth=None,
    source=None,
    field=None,
    output_filename_template="temp/{prefix}{identifier}.tsv",
) -> list:
    """
    Generalized function to create words to add lists with various configurations.

    Parameters:
    - db_session: The database session for retrieving inflections.
    - pth: Path for resources.
    - make_cst_func: Function to create the CST text list.
    - make_sc_func: Optional function to create the SC text list.
    - inflection_func: Function to generate the inflection set.
    - book: The book name (optional).
    - sutta_name: The sutta name (optional).
    - dpspth: Path for DPS files (optional).
    - source: Source identifier (optional).
    - field: Field name for inflections (optional).
    - output_filename_template: Template for the output file name.

    Returns:
    - A sorted list of words to add.
    """
    # Generate CST and SC text lists
    if dpspth:
        cst_text_list = make_cst_func(dpspth)
    elif sutta_name:
        cst_text_list = make_cst_func(pth, sutta_name, [book])
    else:
        cst_text_list = make_cst_func(pth, [book])

    sc_text_list = make_sc_func(pth, [book]) if make_sc_func else []
    original_text_list = list(cst_text_list) + list(sc_text_list)

    # Generate additional lists
    sp_mistakes_list = make_sp_mistakes_list(pth)
    variant_list = make_variant_list(pth)
    sandhi_ok_list = make_sandhi_ok_list(pth)

    # Conditionally pass arguments to the inflection function
    if "filtered" in inflection_func.__name__:
        all_inflections_set = inflection_func(db_session, source=source)
    elif "field" in inflection_func.__name__:
        all_inflections_set = inflection_func(db_session, field=field)
    else:
        all_inflections_set = inflection_func(db_session)

    # Filter the text set
    text_set = set(cst_text_list) | set(sc_text_list)
    text_set -= set(sandhi_ok_list)
    text_set -= set(sp_mistakes_list)
    text_set -= set(variant_list)
    text_set -= all_inflections_set

    # Sort based on original order
    text_list = sorted(text_set, key=lambda x: original_text_list.index(x))

    print(f"words_to_add: {len(text_list)}")

    # Determine filename
    prefix = "dps_" if "dps" in inflection_func.__name__ else ""
    identifier = (
        f"{source}_{book}" if source else 
        f"{sutta_name}_{book}" if sutta_name else 
        f"text_{field}" if field else 
        book or "text"
    )
    output_filename = output_filename_template.format(prefix=prefix, identifier=identifier)

    # Save to a file
    with open(output_filename, "w") as f:
        for word in text_list:
            f.write(f"{word}\n")

    return text_list


def make_sp_mistakes_list(pth):

    with open(pth.spelling_mistakes_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sp_mistakes_list = [row[0] for row in reader]

    print(f"sp_mistakes_list: {len(sp_mistakes_list)}")
    return sp_mistakes_list


def make_variant_list(pth):
    with open(pth.variant_readings_path) as f:
        reader = csv.reader(f, delimiter="\t")
        variant_list = [row[0] for row in reader]

    print(f"variant_list: {len(variant_list)}")
    return variant_list


def make_sandhi_ok_list(pth):
    with open(pth.decon_checked) as f:
        reader = csv.reader(f, delimiter="\t")
        sandhi_ok_list = [row[0] for row in reader]

    print(f"sandhi_ok_list: {len(sandhi_ok_list)}")
    return sandhi_ok_list