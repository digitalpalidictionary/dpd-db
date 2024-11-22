"""Functions related to the GUI (DPS) old."""

from rich import print

from db.models import DpdHeadword

from gui.functions_db_dps import read_ids_from_tsv
from gui.functions_db_dps import remove_duplicates



#! maybe remove?
def update_words_value(dpspth, db_session, WHAT_TO_UPDATE, SOURCE):
    # Fetch the matching words
    ordered_ids = read_ids_from_tsv(dpspth.id_to_add_path)
    ordered_ids = remove_duplicates(ordered_ids)

    print(WHAT_TO_UPDATE)
    print(SOURCE)

    updated_count = 0

    for word_id in ordered_ids:
        word = db_session.query(DpdHeadword).filter(DpdHeadword.id == word_id).first()
        if not word or not word.sbs:
            continue

        attr_value = getattr(word.sbs, WHAT_TO_UPDATE, None)

        all_examples_present = all([
            getattr(word.sbs, 'sbs_example_1', None),
            getattr(word.sbs, 'sbs_example_2', None),
            getattr(word.sbs, 'sbs_example_3', None),
            getattr(word.sbs, 'sbs_example_4', None)
        ])

        print(f"Checking word ID: {word_id}")
        print(f"all_examples_present: {all_examples_present}")
        print(f"attr_value: {attr_value}")

        if all_examples_present and not attr_value:
            setattr(word.sbs, WHAT_TO_UPDATE, SOURCE)
            updated_count += 1
            print(f"{word.id} - {WHAT_TO_UPDATE} with {SOURCE}", flush=True)

    db_session.close()
    print(f"{updated_count} rows have been updated with {SOURCE}.")


#! maybe remove?
def print_words_value(dpspth, db_session, WHAT_TO_UPDATE, SOURCE):
    # Fetch the matching words
    ordered_ids = read_ids_from_tsv(dpspth.id_to_add_path)
    ordered_ids = remove_duplicates(ordered_ids)

    print(WHAT_TO_UPDATE)
    print(SOURCE)

    for word_id in ordered_ids:
        word = db_session.query(DpdHeadword).filter(DpdHeadword.id == word_id).first()
        if not word or not word.sbs:
            continue

        attr_value = getattr(word.sbs, WHAT_TO_UPDATE, None)

        all_examples_present = all([
            getattr(word.sbs, 'sbs_example_1', None),
            getattr(word.sbs, 'sbs_example_2', None),
            getattr(word.sbs, 'sbs_example_3', None),
            getattr(word.sbs, 'sbs_example_4', None)
        ])
        if all_examples_present and not attr_value:
            setattr(word.sbs, WHAT_TO_UPDATE, SOURCE)
            print(f"{word.id} - {WHAT_TO_UPDATE} with {SOURCE}", flush=True)
