"""Add user additions to db, saving the old & new IDs."""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord

from tools.paths import ProjectPaths
from tools.addition_class import Addition


def main():
    print("[bright_yellow]add additions to db")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # get the very last id number
    last_id = max(db_session.query(PaliWord.id).all())[0]
    next_id = last_id + 1
    print(f"{'last_id:':<20}{last_id:>10}")
    print(f"{'next_id:':<20}{next_id:>10}")

    # open the additions pickle file
    additions_list = Addition.load_additions()
    
    added_count = 0
    for a in additions_list:
        a : Addition
        p = a.pali_word

        # check if it's added
        if not a.added_to_db:

            # update the id
            p.id = next_id
            
            # always use meaning_1
            if not p.meaning_1:
                p.meaning_1 = p.meaning_2
            a.update(next_id)
            
            print(a)

            # add it to the session
            db_session.add(p)

            # increment the id
            next_id = next_id + 1
            added_count += 1

    Addition.save_additions(additions_list)

    db_session.commit()
    print(f"{'added:':<20}{added_count:>10}")


if __name__ == "__main__":
    main()
