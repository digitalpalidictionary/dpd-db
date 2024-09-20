#!/usr/bin/env python3

"""Restore db from Ankti database in case of emergency."""

from datetime import datetime, timedelta
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc, bip, bop

from scripts.build.anki_updater import setup_anki_updater

def main():
    tic()
    print("[bright_yellow]updating anki")

    # setup dbs
    bip()
    print(f"[green]{'setup dbs':<20}", end="")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    print(f"{len(db):>10}{bop():>10.2f}")

    decks = ["Vocab", "Commentary", "Pass1"]
    (
        col,
        data_dict,
        deck_dict,
        model_dict,
        carry_on
    ) = setup_anki_updater(decks)

    # # update words
    count = 0
    for counter, i in enumerate(db):
        id = str(i.id)
        if id in data_dict:
            recently_updated = upated_recently(data_dict[id]["note"])
            if recently_updated:
                changed = update_fields(id, i, data_dict)
                if changed:
                    print(f"{count:<4}{i}")
                    count += 1

    # add new words

    new_id = 77298
    for d in data_dict:
        note_id = data_dict[d]["note"]["id"]
        if (
            note_id
            and int(note_id) > 77297 
        ):

            word_to_add = add_word(data_dict[d]["note"], new_id)
            if check_unique(db_session, word_to_add):
                db_session.add(word_to_add)
                print(f"[green]{count:<4}{word_to_add}")
            count += 1
            new_id += 1 
    
    # db_session.commit()
    toc()

def check_unique(db_session, i):
    # Check if id and lemma_1 already exist in the database
    existing_word = db_session.query(DpdHeadword)\
        .filter((DpdHeadword.id == i.id) | (DpdHeadword.lemma_1 == i.lemma_1)).first()
    if existing_word is None:
        return True
    else:
        return False


def add_word(note, new_id):
    i = DpdHeadword()
    for attr in dir(i): 
        if attr in note:
            field = note[attr]\
                .replace("<br>", "\n")\
                .replace("&gt;", ">")
            setattr(i, attr, field)
    i.id = new_id
    return i


def upated_recently(note):
   mod_time = datetime.fromtimestamp(note.mod)
   two_days_ago = datetime.now() - timedelta(days=3)
   return mod_time > two_days_ago


def update_fields(id: str, i: DpdHeadword, data_dict: dict):
    changed_flag = False
    for attr in dir(i): 
        if not attr.startswith('_'):
            dpd_value = getattr(i, attr)
            anki_value = data_dict[id]["note"][attr] if attr in data_dict[id]["note"] else None
            
            # cleanup
            if anki_value and isinstance(dpd_value, int):
                continue
            if anki_value and "<br>" in anki_value:
                anki_value = anki_value.replace("<br>", "\n")
            if attr == "root_key":
                continue
            if attr == "sanskrit":
                continue
            if anki_value and "&gt;" in anki_value:
                continue
            
            if dpd_value != anki_value:
                if dpd_value is not None and anki_value is not None:
                    # print(f"{pali_word.lemma_1}")
                    # print(f"[white]{dpd_value:<20}")
                    # print(f"[green]{anki_value:<20}")
                    setattr(i, attr, anki_value)
                    changed_flag = True
    return changed_flag


if __name__ == "__main__":
    main()
