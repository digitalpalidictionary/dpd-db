#!/usr/bin/env python3

"""Update Anki with latest data directly from the DB."""

import copy

from anki.collection import Collection
from anki.errors import DBError
from anki.notes import Note
from anki.cards import Card

from rich import print
from typing import List, Dict

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.configger import config_read, config_test
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc, bip, bop


def main():
    tic()
    print("[bright_yellow]updating anki")

    # setup dbs
    bip()
    print(f"[green]{'setup dbs':<20}", end="")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    print(f"{'ok':>10}{bop():>10}")

    decks = ["Vocab", "Commentary", "Pass1"]
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


def family_updater(anki_data_list, deck):
    print(f"[white]updating {deck[0].lower()}")
    (
        col,
        data_dict,
        deck_dict,
        model_dict,
        carry_on
    ) = setup_anki_updater(deck)

    if carry_on:
        update_family(
            col,
            deck,
            data_dict,
            deck_dict,
            model_dict,
            anki_data_list)

        if col:
            col.close()
    else:
        return

        
def get_anki_collection() -> Collection|None:
    bip()
    print(f"[green]{'get anki collection':<20}", end="")
    anki_db_path = config_read("anki", "db_path")
    try:
        col = Collection(anki_db_path)
        print(f"{'ok':>10}{bop():>10}")
        return col
    except DBError:
        print("\n[red]Anki is currently open, ", end="")
        print("close and try again.")
        return None


def backup_anki_db(col) -> None:
    """backup anki db"""
    bip()
    print(f"[green]{'backup anki db':<20}", end="")
    anki_backup_path = config_read("anki", "backup_path")
    if anki_backup_path:
        is_backed_up = col.create_backup(backup_folder=anki_backup_path, force=False, wait_for_completion=False)
        # if force = False, the db will not backup if it has not changed
        if not is_backed_up:
            print(f"[red]{'no':>10}{bop():>10}")
        else:
            print(f"{'ok':>10}{bop():>10}")
    else:
        print(f"[red]{'no path':>10}{bop():>10}")


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
    
    print(f"{len(notes):>10}{bop():>10}")
    return notes


def get_cards(col: Collection, decks: List[str]) -> List[Card]:
    """get all cards for a list of decks"""
    bip()
    print(f"[green]{'get cards':<20}", end="")
    
    search_query =  make_search_query(decks)
    card_ids = col.find_cards(search_query)
    cards = [col.get_card(card_id) for card_id in card_ids]
    
    print(f"{len(cards):>10}{bop():>10}")
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
    
    print(f"{len(deck_dict_reverse):>10}{bop():>10}")
    return deck_dict


def get_models(col: Collection) -> dict:
    # get models
    bip()
    print(f"[green]{'get models':<20}", end="")
    
    models = col.models.all()
    model_dict = {model["name"]: model["id"] for model in models}
    
    print(f"{len(model_dict):>10}{bop():>10}")
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
    print(f"{len(data_dict):>10}{bop():>10}")
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
                note, is_updated = update_note_values(col, note, i)
                if is_updated:
                    updated_list += [i.id]
                    col.update_note(note)
                if update_deck(col, note, i, data_dict[id], deck_dict, model_dict):
                    changed_deck_list += [i.id]
                
            # add note
            else:
                added_list += [i.id]
                make_new_note(col, deck, model_dict, deck_dict, i)
            if counter % 5000 == 0:
                print(f"{counter:>5} {i.lemma_1[:23]:<24}{bop():>10}")
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


def update_family(
        col,
        deck,
        data_dict,
        deck_dict,
        model_dict,
        anki_data
) -> None:    

    bip()
    print("[green]updating anki collection")
    
    added_list = []
    updated_list = []
    deleted_list = []

    for i in anki_data:
        key, html = i
        if key in data_dict:
            note = data_dict[key]["note"]
            note, is_updated = update_family_note(note, i)
            if is_updated:
                updated_list += [key]
                col.update_note(note)
            
            # add note
        else:
            added_list += [key]
            make_new_family_note(col, deck, model_dict, deck_dict, i)

    for key, data in data_dict.items():
        if data["note"]["Front"] not in [item[0] for item in anki_data]:
            note = data["note"]
            col.remove_notes([note.id])
            deleted_list += [key]

    print(f"[green]{'added':<20}{len(added_list):>10}")
    print(f"[green]{'updated':<20}{len(updated_list):>10}")
    print(f"[green]{'deleted':<20}{len(deleted_list):>10}")
    print(f"{added_list=}")
    print(f"{updated_list=}")
    print(f"{deleted_list=}")


def update_note_values(col, note, i):
    old_fields = copy.copy(note.fields)
    if i.meaning_1 and i.sutta_1:
        fin = "√√"
    elif i.meaning_1 and not i.sutta_1:
        fin = "√"
    else:
        fin = ""
    
    note["id"] = str(i.id)
    note["lemma_1"] = str(i.lemma_1)
    note["lemma_2"] = str(i.lemma_2)
    note["fin"] = fin
    note["pos"] = str(i.pos)
    note["grammar"] = str(i.grammar)
    note["derived_from"] = str(i.derived_from)
    note["neg"] = str(i.neg)
    note["verb"] = str(i.verb)
    note["trans"] = str(i.trans)
    note["plus_case"] = str(i.plus_case)
    note["meaning_1"] = str(i.meaning_1)
    note["meaning_lit"] = str(i.meaning_lit)
    note["non_ia"] = str(i.non_ia)
    note["sanskrit"] = str(i.sanskrit)
    note["root_key"] = str(i.root_clean)
    note["root_sign"] = str(i.root_sign)
    note["root_base"] = str(i.root_base)
    if i.root_key:
        note["sanskrit_root"] = str(i.rt.sanskrit_root)
        note["sanskrit_root_meaning"] = str(i.rt.sanskrit_root_meaning)
        note["sanskrit_root_class"] = str(i.rt.sanskrit_root_class)
        note["root_meaning"] = str(i.rt.root_meaning)
        note["root_in_comps"] = str(i.rt.root_in_comps)
        note["root_has_verb"] = str(i.rt.root_has_verb)
        note["root_group"] = str(i.rt.root_group)
    note["family_root"] = str(i.family_root)
    note["family_word"] = str(i.family_word)
    note["family_compound"] = str(i.family_compound)
    note["family_idioms"] = str(i.family_idioms)
    note["construction"] = str(i.construction).replace("\n", "<br>")
    note["derivative"] = str(i.derivative)
    note["suffix"] = str(i.suffix)
    note["phonetic"] = str(i.phonetic).replace("\n", "<br>")
    note["compound_type"] = str(i.compound_type)
    note["compound_construction"] = str(i.compound_construction)
    note["non_root_in_comps"] = str(i.non_root_in_comps)
    note["source_1"] = str(i.source_1)
    note["sutta_1"] = str(i.sutta_1).replace("\n", "<br>")
    note["example_1"] = str(i.example_1).replace("\n", "<br>")
    note["source_2"] = str(i.source_2)
    note["sutta_2"] = str(i.sutta_2).replace("\n", "<br>")
    note["example_2"] = str(i.example_2).replace("\n", "<br>")
    note["antonym"] = str(i.antonym)
    note["synonym"] = str(i.synonym)
    note["variant"] = str(i.variant)
    note["commentary"] = str(i.commentary).replace("\n", "<br>")
    note["notes"] = str(i.notes).replace("\n", "<br>")
    note["cognate"] = str(i.cognate)
    note["family_set"] = str(i.family_set)
    note["link"] = str(i.link).replace("\n", "<br>")
    note["stem"] = str(i.stem)
    note["pattern"] = str(i.pattern)
    note["meaning_2"] = str(i.meaning_2)
    note["origin"] = str(i.origin)
    is_updated = None
    if note.fields == old_fields:
        is_updated = False
    elif note.fields != old_fields:
        is_updated = True
        def unicode_combo_characters():
            for index, (old_value, new_value) in enumerate(zip(old_fields, note.fields)):
                if old_value != new_value:
                    print(f"Field at index {index} has changed:")
                    print(f"  Old value: {old_value}")
                    print(f"  New value: {new_value}")
        # unicode_combo_characters()
    return note, is_updated


def update_family_note(note, i):
    old_fields = copy.copy(note.fields)
    key, html = i

    note["Front"] = key
    note["Back"] = html

    is_updated = None
    if note.fields == old_fields:
        is_updated = False
    elif note.fields != old_fields:
        is_updated = True
    return note, is_updated


def deck_selector(i):
    """Choose the deck based on meaning and examples."""
    if i.meaning_1 and i.example_1:
        return "Vocab"
    elif i.meaning_1 and not i.source_1:
        return "Commentary"
    elif not i.meaning_1 and i.origin == "pass1":
        return "Pass1"
    else:
        return None


def update_deck(col, note, i, data, deck_dict, model_dict):
    """When deck changes, update."""
    new_deck = deck_selector(i)
    old_deck = deck_dict[data["did"]]

    if old_deck != new_deck:

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
        return False


def make_new_note(col, deck, model_dict, deck_dict, i):
    """Make a new note."""
    model_id = model_dict[deck]
    deck_id = deck_dict[deck]
    note = col.new_note(model_id)
    note, is_updated = update_note_values(col, note, i)
    col.add_note(note, deck_id)


def make_new_family_note(col, deck, model_dict, deck_dict, i):
    """Make a new note for family decks."""
    deck = deck[0]
    model_id = model_dict[deck]
    deck_id = deck_dict[deck]
    note = col.new_note(model_id)
    note, is_updated = update_family_note(note, i)
    col.add_note(note, deck_id)


if __name__ == "__main__":
    if config_test("anki", "update", "yes"):
        main()
    else:
        print("[green]disabled in the config")
