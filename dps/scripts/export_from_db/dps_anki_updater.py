#!/usr/bin/env python3

"""Update DPS Anki deck with latest data directly from the DB."""

import copy
import os
import datetime
import sys

from anki.collection import Collection
from anki.errors import DBError
from anki.notes import Note
from anki.cards import Card

from rich import print
from typing import List, Dict

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.configger import config_read
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from tools.tic_toc import tic, toc, bip, bop

from sqlalchemy.orm import joinedload

# Check if 'test' argument is provided
update_test_field = 'test' in sys.argv

current_date = datetime.date.today().strftime("%m-%d")

dpspth = DPSPaths()


def main():
    tic()
    print("[bright_yellow]updating dps anki")

    # setup dbs
    bip()
    print(f"[green]{'setup dbs':<20}", end="")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)).all()
    print(f"{len(db):>10} {bop()}")

    calculate_index(db, db_session)

    decks = ["Пали Словарь"]
    (
        col,
        data_dict,
        deck_dict,
        model_dict,
        carry_on
    ) = setup_anki_updater(decks)

    if carry_on:
        update_from_db(
            db, col, data_dict, deck_dict, model_dict)

    print(f"test {current_date}")
    
    toc()

    

def setup_anki_updater(decks):
    col = get_anki_collection()
    if col:
        backup_anki_db(col)
        notes = get_notes(col, decks)
        cards = get_cards(col, decks)
        deck_dict = get_decks(col)
        model_dict = get_models(col)
        data_dict = make_data_dict(notes, cards)
        return col, data_dict, deck_dict, model_dict, True
    else:
        return col, {}, {}, {}, False


def get_anki_collection() -> Collection|None:
    bip()
    print(f"[green]{'get anki collection':<20}", end="")
    anki_db_path = config_read("anki", "db_path")
    if anki_db_path:
        try:
            col = Collection(anki_db_path)
            print(f"{'ok':>10} {bop()}")
            return col
        except DBError:
            print("\n[red]Anki is currently open, ", end="")
            print("close and try again.")
            return None

def backup_anki_db(col) -> None:
    # backup anki db
    bip()
    print(f"[green]{'backup anki db':<20}", end="")
    anki_backup_path = config_read("anki", "backup_path")
    if anki_backup_path:
        is_backed_up = col.create_backup(backup_folder=anki_backup_path, force=False, wait_for_completion=False)
        # if force = False, the db will not backup if it has not changed
        if not is_backed_up:
            print(f"[red]{'no':>10} {bop()}")
        else:
            print(f"{'ok':>10} {bop()}")
    else:
        print(f"[red]{'no path':>10} {bop()}")

def get_field_names(col: Collection, deck_name: str) -> List[str]:
    """get field names for a specif deck"""
    note_ids = col.find_notes(f"deck:{deck_name}")
    if note_ids:
        note_id = note_ids[0]
        note = col.get_note(note_id)
        field_names = note.keys()
        return field_names
    else:
        return []

def make_search_query(decks):
    return " or ".join(f'deck:"{deck}"' for deck in decks)

def get_notes(col: Collection, decks: List[str]) -> List[Note]:
    """get all notes for a list of decks"""
    bip()
    print(f"[green]{'get notes':<20}", end="")
    search_query =  make_search_query(decks)
    note_ids = col.find_notes(search_query)
    notes = [col.get_note(note_id) for note_id in note_ids]
    print(f"{len(notes):>10} {bop()}")
    return notes

def get_cards(col: Collection, decks: List[str]) -> List[Card]:
    """get all cards for a list of decks"""
    bip()
    print(f"[green]{'get cards':<20}", end="")
    search_query =  make_search_query(decks)
    card_ids = col.find_cards(search_query)
    cards = [col.get_card(card_id) for card_id in card_ids]
    print(f"{len(cards):>10} {bop()}")
    return cards

def get_decks(col: Collection) -> Dict:
    """get all decks"""
    bip()
    print(f"[green]{'get decks':<20}", end="")
    decks = col.decks.all()
    deck_dict = {deck["name"]: deck["id"] for deck in decks}
    # add the values as keys
    deck_dict_reverse = {}
    for deck, did in deck_dict.items():
        deck_dict_reverse[did] = deck
    deck_dict.update(deck_dict_reverse)
    print(f"{len(deck_dict_reverse):>10} {bop()}")
    return deck_dict

def get_models(col: Collection) -> dict:
    # get models
    bip()
    print(f"[green]{'get models':<20}", end="")
    models = col.models.all()
    model_dict = {model["name"]: model["id"] for model in models}
    print(f"{len(model_dict):>10} {bop()}")
    return model_dict

def make_data_dict(
        notes: List[Note],
        cards: List[Card]) -> dict:
    """make data dict"""

    bip()
    print(f"[green]{'make data_dict':<20}", end="")
    data_dict = {}

    for note in notes:
        data_dict[note.id] = {
            "nid": note.id,
            "dpd_id": note.fields[0],
            "mid": note.mid,
            "guid": note.guid,
            "note": note,
            "cid": None,
            "did": None,
            "card": None,
        }
    
    for card in cards:
        if card.nid in data_dict:
            data_dict[card.nid]["cid"] = card.id
            data_dict[card.nid]["did"] = card.did
            data_dict[card.nid]["card"] = card

    # re-key data_dict
    data2 = {}
    for key, data, in data_dict.items():
        dpd_id = data["dpd_id"]
        if dpd_id in data_dict:
            print(f"[red]key {dpd_id} already exists")
        else:
            data2[dpd_id] = data
    for key in data2:
        if key in data_dict:
            print("Key", key, "will be overwritten")
    data_dict.update(data2)
    print(f"{len(data_dict):>10} {bop()}")
    return data_dict

def update_from_db(db, col, data_dict, deck_dict, model_dict) -> None:    
    # update from db
    bip()
    print(f"[green]{'updating':<20}")
    added_list = []
    updated_list = []
    deleted_list = []
    changed_deck_list = []
    for counter, i in enumerate(db):
        id = str(i.id)
        deck = deck_selector(i)
        if deck:
            # update
            if id in data_dict:
                note = data_dict[id]["note"]
                note, is_updated = update_note_values(note, i)
                if is_updated:
                    updated_list += [i.id]
                    col.update_note(note)
                if update_deck(col, note, i, data_dict[id], deck_dict, model_dict):
                    changed_deck_list += [i.id]
                
            # add note
            else:
                added_list += [i.id]

                # print(f"Model Dictionary:, {model_dict}")

                make_new_note(col, deck, model_dict, deck_dict, i)
            if counter % 5000 == 0:
                print(f"{counter:>5} {i.lemma_1[:23]:<24} {bop()}")
                bip()

        else:
            # delete
            if i.id in data_dict:
                print(data_dict[id])
                deleted_list += [i.id]

    print(f"[green]{'added':<20}{len(added_list):>10}")
    print(f"[green]{'updated':<20}{len(updated_list):>10}")
    print(f"[green]{'changed deck':<20}{len(changed_deck_list):>10}")
    print(f"[green]{'deleted':<20}{len(deleted_list):>10}")

    print(f"{added_list=}")
    print(f"{updated_list=}")
    print(f"{changed_deck_list=}")
    print(f"{deleted_list=}")


def update_note_values(note, i):
    old_fields = copy.copy(note.fields)
    tags = ""
    tags = " ".join(note.tags)  # Convert list of tags to a single string

    note["id"] = str(i.id)
    note["pali"] = str(i.lemma_1)
    if i.ru:
        note["ru_meaning"] = str(i.ru.ru_meaning)
        note["ru_meaning_lit"] = str(i.ru.ru_meaning_lit)
        note["ru_notes"] = str(i.ru.ru_notes).replace("\n", "<br>")

    if i.sbs:
        note["sbs_meaning"] = str(i.sbs.sbs_meaning)
        note["sbs_class_anki"] = str(i.sbs.sbs_class_anki)
        note["sbs_category"] = str(i.sbs.sbs_category)
        note["sbs_class"] = str(i.sbs.sbs_class)
        note["sbs_patimokkha"] = str(i.sbs.sbs_patimokkha)
        note["sbs_source_1"] = str(i.sbs.sbs_source_1)
        note["sbs_sutta_1"] = str(i.sbs.sbs_sutta_1).replace("\n", "<br>")
        note["sbs_example_1"] = str(i.sbs.sbs_example_1).replace("\n", "<br>")
        note["sbs_chant_pali_1"] = str(i.sbs.sbs_chant_pali_1)
        note["sbs_chant_eng_1"] = str(i.sbs.sbs_chant_eng_1)
        note["sbs_chapter_1"] = str(i.sbs.sbs_chapter_1)
        note["sbs_source_2"] = str(i.sbs.sbs_source_2)
        note["sbs_sutta_2"] = str(i.sbs.sbs_sutta_2).replace("\n", "<br>")
        note["sbs_example_2"] = str(i.sbs.sbs_example_2).replace("\n", "<br>")
        note["sbs_chant_pali_2"] = str(i.sbs.sbs_chant_pali_2)
        note["sbs_chant_eng_2"] = str(i.sbs.sbs_chant_eng_2)
        note["sbs_chapter_2"] = str(i.sbs.sbs_chapter_2)
        note["sbs_source_3"] = str(i.sbs.sbs_source_3)
        note["sbs_sutta_3"] = str(i.sbs.sbs_sutta_3).replace("\n", "<br>")
        note["sbs_example_3"] = str(i.sbs.sbs_example_3).replace("\n", "<br>")
        note["sbs_chant_pali_3"] = str(i.sbs.sbs_chant_pali_3)
        note["sbs_chant_eng_3"] = str(i.sbs.sbs_chant_eng_3)
        note["sbs_chapter_3"] = str(i.sbs.sbs_chapter_3)
        note["sbs_source_4"] = str(i.sbs.sbs_source_4)
        note["sbs_sutta_4"] = str(i.sbs.sbs_sutta_4).replace("\n", "<br>")
        note["sbs_example_4"] = str(i.sbs.sbs_example_4).replace("\n", "<br>")
        note["sbs_chant_pali_4"] = str(i.sbs.sbs_chant_pali_4)
        note["sbs_chant_eng_4"] = str(i.sbs.sbs_chant_eng_4)
        note["sbs_chapter_4"] = str(i.sbs.sbs_chapter_4)
        note["sbs_notes"] = str(i.sbs.sbs_notes).replace("\n", "<br>")
        note["sbs_index"] = str(i.sbs.sbs_index)

    note["grammar"] = str(i.grammar)
    note["neg"] = str(i.neg)
    note["verb"] = str(i.verb)
    note["trans"] = str(i.trans)
    note["plus_case"] = str(i.plus_case)

    # 'meaning_1' field
    if i.ru:
        if (
            not i.meaning_1 and 
            i.meaning_lit and 
            " lit." in i.meaning_2
        ):
            # Remove everything after " lit." in 'meaning_2'
            meaning_2_without_lit = i.meaning_2.split("; lit.")[0]
            note['meaning'] = meaning_2_without_lit
            # print(f"meaning_2_without_lit {i.lemma_1}") # Debugging line
        elif (
            not i.meaning_1 and 
            i.meaning_lit and 
            i.meaning_2
        ):
            note['meaning'] = i.meaning_2
            # print(f"meaning_2=meaning_1 {i.lemma_1}") # Debugging line
        elif (
            not i.meaning_1 and 
            not i.meaning_lit and 
            i.meaning_2
        ):
            note['meaning'] = i.meaning_2
            # print(f"meaning_2=meaning_1 {i.lemma_1}") # Debugging line

        elif i.meaning_1:
            note['meaning'] = i.meaning_1
            # print(f"meaning_1 {i.lemma_1}") # Debugging line
        else:
            print(f"no meaning {i.lemma_1}")
        
    note["meaning_lit"] = str(i.meaning_lit)
    note["sanskrit"] = str(i.sanskrit)
    note["root"] = str(i.root_clean)
    note["root_sign"] = str(i.root_sign)
    note["root_base"] = str(i.root_base)
    if i.root_key:
        note["sanskrit_root"] = str(i.rt.sanskrit_root)
        note["sanskrit_root_meaning"] = str(i.rt.sanskrit_root_meaning)
        note["sanskrit_root_ru_meaning"] = str(i.rt.sanskrit_root_ru_meaning)
        note["sanskrit_root_class"] = str(i.rt.sanskrit_root_class)
        note["root_meaning"] = str(i.rt.root_meaning)
        note["root_ru_meaning"] = str(i.rt.root_ru_meaning)
        note["root_has_verb"] = str(i.rt.root_has_verb)
        note["root_group"] = str(i.rt.root_group)
    note["construction"] = str(i.construction).replace("\n", "<br>")
    note["derivative"] = str(i.derivative)
    note["suffix"] = str(i.suffix)
    note["phonetic"] = str(i.phonetic).replace("\n", "<br>")
    note["compound_type"] = str(i.compound_type)
    note["compound_construction"] = str(i.compound_construction)
    note["antonym"] = str(i.antonym)
    note["synonym"] = str(i.synonym)
    note["variant"] = str(i.variant)
    note["commentary"] = str(i.commentary).replace("\n", "<br>")
    note["notes"] = str(i.notes).replace("\n", "<br>")
    if update_test_field:
        note["test"] = str(current_date)

    # 'link' field
    if i.link:
        note['link'] = f'<a class="link" href="{i.link}">Wiki link</a>'
    else:
        note['link'] = ''

    #! UPDATING TAGS NOT WORKING!
    # adding _SBS tag if pubbakicca index is 75
    if i.sbs and i.sbs.sbs_index and i.sbs.sbs_index != 75:
        if not any(tag.startswith("_SBS") or tag.startswith("*parit") for tag in tags.split()):
            if tags:
                tags += " "
            tags += "_SBS"
            note.tags = tags.split()
            
    # adding _pātimokkha tag if PAT is in the source
    if i.sbs:
        sources = [i.sbs.sbs_source_1, i.sbs.sbs_source_2, i.sbs.sbs_source_3, i.sbs.sbs_source_4]
        if any("PAT" in source for source in sources):
            if not any(tag.startswith("_pātimokkha") for tag in tags.split()):
                if tags:
                    tags += " "
                tags += "_pātimokkha"
                note.tags = tags.split()

        # removing _pātimokkha tag if PAT is not in the source
        else:
            if "_pātimokkha" in tags.split():
                tags = " ".join(tag for tag in tags.split() if not tag.startswith("_pātimokkha"))
                note.tags = tags.split()


    # sbs_audio
    if dpspth.anki_media_dir:
        audio_path = os.path.join(dpspth.anki_media_dir, f"{i.lemma_clean}.mp3")
        if os.path.exists(audio_path):
            sbs_audio = f"[sound:{i.lemma_clean}.mp3]"
        else:
            sbs_audio = ''
    else:
        print("[bold red]no path to anki media")
        sbs_audio = ''

    note["audio"] = sbs_audio

    # Logic for feedback
    feedback_url = f'Нашли ошибку? <a class="link" href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&entry.438735500={i.lemma_1}&entry.1433863141=Anki-{current_date}\">Пожалуйста сообщите</a>.'
    if update_test_field:
        note["feedback"] = feedback_url

    is_updated = None
    if note.fields == old_fields:
        is_updated = False
    elif note.fields != old_fields:
        is_updated = True
        # unicode_combo_characters(old_fields, note)  # Debugging function

    return note, is_updated


def unicode_combo_characters(old_fields, note):
    for index, (old_value, new_value) in enumerate(zip(old_fields, note.fields)):
        if old_value != new_value:
            print(f"> index {index} has changed:")
            print(f"> Old value: {old_value}")
            print(f"> New value: {new_value}")


def calculate_index(db, db_session):
    """
    Recalculates the sbs_index for all entries in the db and commits the changes.
    
    """

    print("[green]Calculating sbs_index")
    try:
        for i in db:
            if i.sbs:
                sbs_index_old = i.sbs.sbs_index
                sbs_index_value = i.sbs.calculate_index()
                if sbs_index_old != sbs_index_value:
                    i.sbs.sbs_index = sbs_index_value  # Manually set the sbs_index
                    print(f"{i.lemma_1} old index {sbs_index_old} changed to {sbs_index_value}")
    
        db_session.commit()
        
    except Exception as e:
        print(f"[bold red]{str(e)}")


def deck_selector(i):
    if (i.ru and i.ru.ru_meaning 
    and i.sbs 
    and(
            i.sbs.sbs_example_1 or 
            i.sbs.sbs_example_2 or 
            i.sbs.sbs_example_3 or 
            i.sbs.sbs_example_4
        )
    ):
        return "Пали Словарь"
    else:
        return None


def update_deck(col, note, i, data, deck_dict, model_dict):
    new_deck = deck_selector(i)
    old_deck = deck_dict[data["did"]]

    if old_deck != new_deck:
        # Check if new_deck exists in model_dict before accessing it
        if new_deck in model_dict:
            # update note
            note.mid = model_dict[new_deck]
            col.update_note(note)
            
            # update card
            card = data["card"]
            card.did = deck_dict[new_deck]
            card.queue = 0
            card.lapse = 0
            card.due = 0
            col.update_card(card)

            return True
        else:
            # print(f"Warning: Deck '{new_deck}' not found in model_dict.")  # Debugging line
            return False

    else:
        return False


def make_new_note(col, deck, model_dict, deck_dict, i):
    
    print(f"Creating new note for {i.lemma_1}") # Debugging line

    note_type_name = "Pāli"

    # print(f"Deck: {deck}") # Debugging line

    # print(f"Model Dictionary: {model_dict}") # Debugging line

    if note_type_name in model_dict:
        model_id = model_dict[note_type_name]
        deck_id = deck_dict[deck]
        note = col.new_note(model_id)
        note, is_updated = update_note_values(note, i)
        col.add_note(note, deck_id)

        # print(f"Added new note for {i.lemma_1}") # Debugging line

    else:
        print(f"Warning: Note type '{note_type_name}' not found in model_dict. for {i.lemma_1}")


if __name__ == "__main__":
    main()
