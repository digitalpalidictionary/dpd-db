"""Database functions related to the GUI.(DPS)."""

import csv
import re

from rich import print

from typing import Optional

from sqlalchemy import not_, or_, and_
from sqlalchemy.orm import joinedload

from db.db_helpers import get_column_names
from db.models import Russian, SBS, DpdHeadword

from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_sc_text_sets import make_cst_text_list_from_file
from tools.cst_sc_text_sets import make_cst_text_list_sutta
from tools.cst_sc_text_sets import make_sc_text_list
from tools.meaning_construction import make_meaning_combo
from tools.tsv_read_write import read_tsv_dot_dict
from tools.fast_api_utils import request_dpd_server
from tools.pali_sort_key import pali_sort_key

from gui.functions_db import make_words_to_add_list_generic
from gui.functions_db import make_all_inflections_set
from gui.functions import stasher

from gui.functions_daily_record import daily_record_update


def populate_dps_tab(dpspth, values, window, dpd_word, ru_word, sbs_word):
    """Populate DPS tab with DPD info."""
    window["dps_dpd_id"].update(dpd_word.id)
    window["dps_lemma_1"].update(dpd_word.lemma_1)
    window["dps_id_or_lemma_1"].update(dpd_word.lemma_1)
    if ru_word and ru_word.ru_meaning_raw:
        window["dps_ru_online_suggestion"].update(ru_word.ru_meaning_raw)

    # copy dpd values for tests

    dps_pos = dpd_word.pos
    window["dps_pos"].update(dps_pos)
    dps_family_set = dpd_word.family_set
    window["dps_family_set"].update(dps_family_set)
    dps_suffix = dpd_word.suffix
    window["dps_suffix"].update(dps_suffix)
    dps_verb = dpd_word.verb
    window["dps_verb"].update(dps_verb)
    dps_meaning_lit = dpd_word.meaning_lit
    window["dps_meaning_lit"].update(dps_meaning_lit)
    dps_meaning_1 = dpd_word.meaning_1
    window["dps_meaning_1"].update(dps_meaning_1)


    # grammar
    dps_grammar = dpd_word.grammar
    if dpd_word.neg:
        dps_grammar += f", {dpd_word.neg}"
    if dpd_word.verb:
        dps_grammar += f", {dpd_word.verb}"
    if dpd_word.trans:
        dps_grammar += f", {dpd_word.trans}"
    if dpd_word.plus_case:
        dps_grammar += f" ({dpd_word.plus_case})"
    window["dps_grammar"].update(dps_grammar)

    # meaning
    meaning = make_meaning_combo(dpd_word)
    if dpd_word.meaning_1:
        window["dps_meaning"].update(meaning)
    else:
        meaning = f"(meaing_2) {meaning}"
        window["dps_meaning"].update(meaning)

    # russian
    ru_columns = get_column_names(Russian)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in ru_columns:
                window[value].update(getattr(ru_word, value_clean, ""))

    # sbs
    sbs_columns = get_column_names(SBS)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in sbs_columns:
                window[value].update(getattr(sbs_word, value_clean, ""))

    # root
    root = ""
    if dpd_word.root_key:
        root = f"{dpd_word.root_key} "
        root += f"{dpd_word.rt.root_has_verb} "
        root += f"{dpd_word.rt.root_group} "
        root += f"{dpd_word.root_sign} "
        root += f"({dpd_word.rt.root_meaning} "
        root += f"{dpd_word.rt.root_ru_meaning})"
        if dpd_word.rt.sanskrit_root_ru_meaning:
            root += f"sk {dpd_word.rt.sanskrit_root_ru_meaning}"

    window["dps_root"].update(root)

    # base_or_comp
    base_or_comp = ""
    if dpd_word.root_base:
        base_or_comp += dpd_word.root_base
    elif dpd_word.compound_type:
        base_or_comp += dpd_word.compound_type
    window["dps_base_or_comp"].update(base_or_comp)

    # dps_constr_or_comp_constr
    constr_or_comp_constr = ""
    if dpd_word.compound_construction:
        constr_or_comp_constr += dpd_word.compound_construction
    elif dpd_word.construction:
        constr_or_comp_constr += dpd_word.construction
    window["dps_constr_or_comp_constr"].update(constr_or_comp_constr)

    # synonym_antonym
    dps_syn_ant = ""
    if dpd_word.synonym:
        dps_syn_ant = f"(syn) {dpd_word.synonym}"
    if dpd_word.antonym:
        dps_syn_ant += f"(ant): {dpd_word.antonym}" 
    window["dps_synonym_antonym"].update(dps_syn_ant)

    # notes
    dps_notes = ""
    if dpd_word.notes:
        dps_notes = dpd_word.notes
    window["dps_notes"].update(dps_notes)

    # source_1
    dps_source_1 = ""
    if dpd_word.source_1:
        dps_source_1 = dpd_word.source_1
    window["dps_source_1"].update(dps_source_1)

    # sutta_1
    dps_sutta_1 = ""
    if dpd_word.sutta_1:
        dps_sutta_1 = dpd_word.sutta_1
    window["dps_sutta_1"].update(dps_sutta_1)

    # example_1
    dps_example_1 = ""
    if dpd_word.example_1:
        dps_example_1 = dpd_word.example_1
    window["dps_example_1"].update(dps_example_1)

    # source_2
    dps_source_2 = ""
    if dpd_word.source_2:
        dps_source_2 = dpd_word.source_2
    window["dps_source_2"].update(dps_source_2)

    # sutta_2
    dps_sutta_2 = ""
    if dpd_word.sutta_2:
        dps_sutta_2 = dpd_word.sutta_2
    window["dps_sutta_2"].update(dps_sutta_2)

    # example_2
    dps_example_2 = ""
    if dpd_word.example_2:
        dps_example_2 = dpd_word.example_2
    window["dps_example_2"].update(dps_example_2)

    # dps_sbs_chant_pali
    if values["dps_sbs_chant_pali_1"]:
        chant = values["dps_sbs_chant_pali_1"]
        update_sbs_chant(dpspth, 1, chant, "", window)

    if values["dps_sbs_chant_pali_2"]:
        chant = values["dps_sbs_chant_pali_2"]
        update_sbs_chant(dpspth, 2, chant, "", window)

    if values["dps_sbs_chant_pali_3"]:
        chant = values["dps_sbs_chant_pali_3"]
        update_sbs_chant(dpspth, 3, chant, "", window)

    if values["dps_sbs_chant_pali_4"]:
        chant = values["dps_sbs_chant_pali_4"]
        update_sbs_chant(dpspth, 4, chant, "", window)


# examples related in DPS TABLE
def load_sbs_index(dpspth) -> list:
    file_path = dpspth.sbs_index_path
    sbs_index = read_tsv_dot_dict(file_path)
    return sbs_index


def fetch_sbs_index(dpspth, pali_chant):
    sbs_index = load_sbs_index(dpspth)
    for i in sbs_index:
        if i.pali_chant == pali_chant:
            return i.english_chant, i.chapter
    return None  # explicitly returning None when no match is found


def update_sbs_chant(dpspth, number, chant, error_field, window):
    result = fetch_sbs_index(dpspth, chant)
    if result is not None:
        english, chapter = result
        window[f"dps_sbs_chant_eng_{number}"].update(english)
        window[f"dps_sbs_chapter_{number}"].update(chapter)
    else:
        # handle the case when the chant is not found
        error_message = "chant is not found"
        window[error_field].update(error_message)
        window[f"dps_sbs_chant_eng_{number}"].update("")
        window[f"dps_sbs_chapter_{number}"].update("")


def dps_get_original_values(values, dpd_word, ru_word, sbs_word):

    original_values = {}

    original_values["lemma_1"] = dpd_word.lemma_1

    # For Russian columns
    ru_columns = get_column_names(Russian)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in ru_columns:
                original_values[value_clean] = getattr(ru_word, value_clean, "")

    # For SBS columns
    sbs_columns = get_column_names(SBS)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in sbs_columns:
                original_values[value_clean] = getattr(sbs_word, value_clean, "")
    
    return original_values


# functions which make a list of words from id list
def read_ids_from_tsv(file_path):
    with open(file_path, mode='r', encoding='utf-8-sig') as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        next(tsv_reader)  # Skip header row
        return [int(row[0]) for row in tsv_reader]  # Extracting IDs only from the first column


def remove_duplicates(ordered_ids):
    seen = set()
    ordered_ids_no_duplicates = [x for x in ordered_ids if not (x in seen or seen.add(x))]
    return ordered_ids_no_duplicates


# "from id_temp_list" button Word To Add
def fetch_matching_words_from_db(path, db_session) -> list:

    ordered_ids = read_ids_from_tsv(path)
    ordered_ids = remove_duplicates(ordered_ids)

    matching_words = []
    for word_id in ordered_ids:
        word = db_session.query(DpdHeadword).filter(DpdHeadword.id == word_id).first()
        if word:
            matching_words.append(word.lemma_1)

    print(f"words_to_add: {len(matching_words)}")
    return matching_words


# "from id_to_add" button Word To Add
def fetch_matching_words_from_db_with_conditions(dpspth, db_session, attribute_name, source) -> list:

    ordered_ids = read_ids_from_tsv(dpspth.id_to_add_path)
    ordered_ids = remove_duplicates(ordered_ids)

    matching_words = []
    for word_id in ordered_ids:
        word = db_session.query(DpdHeadword).filter(DpdHeadword.id == word_id).first()
        if word and word.sbs:
            attr_value = getattr(word.sbs, attribute_name, None)
            if attr_value == source or (attr_value is None and source in ["", None]):
                matching_words.append(word.lemma_1)
        if word and not word.sbs:
            matching_words.append(word.lemma_1)

    print(f"words_to_add: {len(matching_words)}")
    return matching_words


# "update" button Word To Add
def update_field(db_session, WHAT_TO_UPDATE, lemma_1, source):

    word = db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == lemma_1).first()

    if word:
        if not word.sbs:
            word.sbs = SBS(id=word.id)
        setattr(word.sbs, WHAT_TO_UPDATE, source)
        db_session.commit()
    
    db_session.close()


# "mark" button Word To Add
def update_field_with_change(db_session, WHAT_TO_UPDATE, lemma_1, source):

    word = db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == lemma_1).first()

    source = source + "_"

    if word:
        if not word.sbs:
            word.sbs = SBS(id=word.id)
        setattr(word.sbs, WHAT_TO_UPDATE, source)
        db_session.commit()
    
    db_session.close()


# "from source" button Word To Add
def words_in_db_from_source(db_session, source):
    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).all()

    matching_words = []

    for i in dpd_db:
        if i.sbs is None or not (
            i.sbs.sbs_source_1 == source or
            i.sbs.sbs_source_2 == source or
            i.sbs.sbs_source_3 == source or
            i.sbs.sbs_source_4 == source
        ):
            if i.source_1 == source or i.source_2 == source:
                matching_words.append(i.lemma_1)

    print(f"from {source} words_to_add: {len(matching_words)}")

    return matching_words


# "source in field" button Word To Add
#! TODO - it is a very fast fetch, redo all other slow in the same way
def words_in_db_with_value_in_field_sbs(db_session, field, source):
    # Ensure the SBS model has the specified field to avoid runtime errors
    if hasattr(SBS, field):
        # Modify the query to include a condition that checks if the field is not empty
        dpd_db = db_session.query(DpdHeadword).join(SBS, DpdHeadword.id == SBS.id).filter(
            # Check if the field is not empty
            not_(getattr(SBS, field).is_(None)),
            not_(getattr(SBS, field) == ''),
            # Check if the field matches the source
            getattr(SBS, field) == source
        ).all()

        matching_words = [i.lemma_1 for i in dpd_db]

        print(f"words with {source} in {field}: {len(matching_words)}")

        return matching_words
    else:
        print(f"The field '{field}' does not exist in the SBS model.")
        return []



# db functions
def fetch_ru(db_session, id: int) -> Optional[Russian]:
    """Fetch Russian word from db."""
    return db_session.query(Russian).filter(
        Russian.id == id).first()


def fetch_sbs(db_session, id: int) -> Optional[SBS]:
    """Fetch SBS word from db."""
    return db_session.query(SBS).filter(
        SBS.id == id).first()


# "Update DB" button DPS
def dps_update_db(
    pth, db_session, values, window, dpd_word, ru_word, sbs_word) -> None:
    """Update Russian and SBS tables with DPS edits."""
    try:
        merge = None
        word_id = values["dps_dpd_id"]
        if not ru_word:
            merge = True
            ru_word = Russian(id=dpd_word.id)
        if not sbs_word:
            sbs_word = SBS(id=dpd_word.id)

        for value in values:
            if value.startswith("dps_ru"):
                attribute = value.replace("dps_", "")
                new_value = values[value]
                setattr(ru_word, attribute, new_value)
            if value.startswith("dps_sbs"):
                attribute = value.replace("dps_", "")
                new_value = values[value]
                setattr(sbs_word, attribute, new_value)

        if merge:
            db_session.merge(ru_word)
            db_session.merge(sbs_word)
        else:
            db_session.add(ru_word)
            db_session.add(sbs_word)

        # Calculate the sbs_index and update the sbs_word object
        sbs_index_value = sbs_word.calculate_index()
        sbs_word.sbs_index = sbs_index_value  # Manually set the sbs_index

        db_session.commit()

        window["messages"].update(
            f"'{values['dps_id_or_lemma_1']}' updated in dps db",
            text_color="Lime")
        daily_record_update(window, pth, "edit", word_id)
        request_dpd_server(values["dps_dpd_id"])

    except Exception as e:
        stasher(pth, values, window)
        window["messages"].update(f"{str(e)}", text_color="red")


# dps_books_to_add_button Word To Add
def dps_make_words_to_add_list(db_session, pth, __window__, book: str) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list,
        make_sc_func=make_sc_text_list,
        inflection_func=dps_make_all_inflections_set,
        book=book
    )


# dps_books_to_add_considering_source_button Word To Add
def dps_make_words_to_add_list_filtered(db_session, pth, __window__, book: str, source) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list,
        make_sc_func=make_sc_text_list,
        inflection_func=dps_make_filtered_inflections_set,
        book=book,
        source=source,
    )


# dps_sutta_to_add_button   Word To Add
def dps_make_words_to_add_list_sutta(db_session, pth, sutta_name, book: str) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list_sutta,
        inflection_func=dps_make_all_inflections_set,
        sutta_name=sutta_name,
        book=book
    )


# sutta_to_add_button   Word To Add
def make_words_to_add_list_sutta(db_session, pth, sutta_name, book: str) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list_sutta,
        inflection_func=make_all_inflections_set,
        sutta_name=sutta_name,
        book=book
    )


# from_txt_to_add_button  Word To Add
def make_words_to_add_list_from_text(dpspth, db_session, pth) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list_from_file,
        dpspth=dpspth
    )


# dps_from_txt_to_add_button  Word To Add
def dps_make_words_to_add_list_from_text(dpspth, db_session, pth) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list_from_file,
        inflection_func=dps_make_all_inflections_set,
        dpspth=dpspth
    )


# "No source" button Word To Add
def dps_make_words_to_add_list_from_text_filtered(dpspth, db_session, pth, source) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list_from_file,
        inflection_func=dps_make_filtered_inflections_set,
        dpspth=dpspth,
        source=source
    )


# "No field" button Word To Add
def dps_make_words_to_add_list_from_text_no_field(dpspth, db_session, pth, field) -> list:
    return make_words_to_add_list_generic(
        db_session=db_session,
        pth=pth,
        make_cst_func=make_cst_text_list_from_file,
        inflection_func=dps_make_no_field_inflections_set,
        dpspth=dpspth,
        field=field
    )


# "ru_synonym" key in DPS
def dps_get_synonyms(db_session, pos: str, string_of_meanings: str, window, error_field) -> Optional[str]:

    string_of_meanings = re.sub(r" \(.*?\)|\(.*?\) ", "", string_of_meanings)
    list_of_meanings = string_of_meanings.split("; ")

    results = db_session.query(DpdHeadword).join(Russian).filter(
            DpdHeadword.pos == pos,
            or_(*[DpdHeadword.meaning_1.like(f"%{meaning}%") for meaning in list_of_meanings]),
            Russian.ru_meaning.isnot(None),  # Ensure ru_meaning is not null
            Russian.ru_meaning != ""         # Ensure ru_meaning is not an empty string
        ).options(joinedload(DpdHeadword.ru)).all()

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

    synonyms = set()
    for key_1 in meaning_dict:
        for key_2 in meaning_dict:
            if key_1 != key_2:
                intersection = meaning_dict[key_1].intersection(
                    meaning_dict[key_2])
                synonyms.update(intersection)

    if not synonyms:
        # Update error_field in window with appropriate message
        window[error_field].update("No synonyms found that fit the filter.")
        return None  # or some other value indicating failure


    synonyms = ", ".join(sorted(synonyms, key=pali_sort_key))
    print(synonyms)
    return synonyms


def dps_make_all_inflections_set(db_session):
    # Generate a set of all inflections in the DPD database where the Russian.ru_meaning is not empty.
    inflections_db = db_session.query(DpdHeadword) \
                            .join(Russian, DpdHeadword.id == Russian.id) \
                            .filter((Russian.ru_meaning.isnot(None)) & 
                                    (Russian.ru_meaning != '')) \
                            .all()

    dps_all_inflections_set = set()
    for i in inflections_db:
        dps_all_inflections_set.update(i.inflections_list)

    print(f"dps_all_inflections_set: {len(dps_all_inflections_set)}")

    return dps_all_inflections_set


def dps_make_filtered_inflections_set(db_session, source):
    """
    Generate a set of all inflections in the DPD database where the specified source is in any of the SBS sources fields,
    but not in any of the SBS sources fields with an 'a' appended to the source.
    """ 
    source_a = source + "a"

    inflections_db = db_session.query(DpdHeadword).join(SBS, DpdHeadword.id == SBS.id).filter(
        and_(
            or_(
                SBS.sbs_source_1.ilike(f"%{source}%"), 
                SBS.sbs_source_2.ilike(f"%{source}%"), 
                SBS.sbs_source_3.ilike(f"%{source}%"), 
                SBS.sbs_source_4.ilike(f"%{source}%"),
                DpdHeadword.source_1.ilike(f"%{source}%"),
                DpdHeadword.source_2.ilike(f"%{source}%"),
            ),
            not_(
                    or_(
                        SBS.sbs_source_1.ilike(f"%{source_a}%"), 
                        SBS.sbs_source_2.ilike(f"%{source_a}%"), 
                        SBS.sbs_source_3.ilike(f"%{source_a}%"), 
                        SBS.sbs_source_4.ilike(f"%{source_a}%"),
                        DpdHeadword.source_1.ilike(f"%{source_a}%"),
                        DpdHeadword.source_2.ilike(f"%{source_a}%"),
                    )
                ),
        )
    ).all()

    dps_filtered_inflections_set = set()
    for i in inflections_db:
        dps_filtered_inflections_set.update(i.inflections_list)

    print(f"dps_filtered_inflections_set: {len(dps_filtered_inflections_set)}")

    return dps_filtered_inflections_set


def dps_make_no_field_inflections_set(db_session, field):
    """
    Generate a set of all inflections in the DPD database where the specified SBS field is not empty.
    """
    
    inflections_db = db_session.query(DpdHeadword).join(SBS, DpdHeadword.id == SBS.id).filter(
        getattr(SBS, field).isnot(None),  
        getattr(SBS, field) != ""       
    ).all()

    dps_filtered_inflections_set = set()
    for i in inflections_db:
        dps_filtered_inflections_set.update(i.inflections_list)

    print(f"dps_filtered_inflections_set: {len(dps_filtered_inflections_set)}")

    return dps_filtered_inflections_set


def get_next_ids_dps(db_session, window):
    # Get all IDs from DpdHeadword table in the database, order them by ID, and find the largest ID.
    used_ids = db_session.query(DpdHeadword.id).order_by(DpdHeadword.id).all()

    def find_largest_id():
        return max(used_id.id for used_id in used_ids) if used_ids else 0

    largest_id = find_largest_id()

    next_id = largest_id + 10000

    print(next_id)

    window["id"].update(next_id)


# "Next Ru" button DPS
def get_next_word_ru(db_session):
    def filter_words():
        return db_session.query(DpdHeadword).join(Russian).join(SBS).filter(
            # DpdHeadword.meaning_1 != "",
            # DpdHeadword.example_1 != "",
            SBS.sbs_patimokkha == "vib_",
            # Russian.ru_meaning == "",
        )

    # Query the database using the helper function
    word = filter_words().first()

    # Query the database to count the total number of words fitting the criteria
    total_words = filter_words().count()

    # Return the id of the word if found, otherwise return None
    if word:
        print(f"id = {word.id}")
        total_words_message = f"words left: {total_words}"
        print(total_words_message)
        return str(word.id), total_words_message
    else:
        total_words_message = "no words left, change filter in functions_dps"
        print(total_words_message)
        return 0, total_words_message


# "Next Note" button DPS
def get_next_note_ru(db_session):
    # Query the database for the first word that meets the conditions
    def filter_words():
        return db_session.query(DpdHeadword).join(Russian).join(SBS).filter(
            Russian.ru_notes.like("%ИИ%"),
            or_(
                    SBS.sbs_class_anki != '',
                    SBS.sbs_category != '',
                    SBS.sbs_index != '',
                    SBS.sbs_patimokkha != '',
                )
            )

    # Query the database using the helper function
    word = filter_words().first()

    # Query the database to count the total number of words fitting the criteria
    total_words = filter_words().count()

    # Return the id of the word if found, otherwise return None
    if word:
        print(f"id = {word.id}")
        total_words_message = f"words left: {total_words}"
        print(total_words_message)
        return str(word.id), total_words_message
    else:
        total_words_message = "no words left, change filter in functions_dps"
        print(total_words_message)
        return 0, total_words_message
