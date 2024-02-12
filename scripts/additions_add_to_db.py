"""Add user additions to db, saving the old & new IDs."""

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords

from tools.paths import ProjectPaths
from tools.addition_class import Addition


def main():
    print("[bright_yellow]add additions to db")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # get the very last id number
    last_id = max(db_session.query(DpdHeadwords.id).all())[0]
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

            if test_pali(db_session, a):
                # increment the id
                next_id = next_id + 1
                added_count += 1

    db_session.commit()
    Addition.save_additions(additions_list)
    print(f"{'added:':<20}{added_count}")


def test_pali(db_session, a):
    """Test if pali_word is in the db already."""

    lemma_1 = a.pali_word.lemma_1
    
    result = db_session.query(DpdHeadwords).filter_by(lemma_1=lemma_1).first() 
    if result:
        print("[red]duplicate lemma_1 found: ", end="")
        print(f"[white]{a.pali_word}")
        print("[white]r[red]ename or [white]d[red]elete? ", end="")
        rename_delete = input ()
        if rename_delete == "d":
            a.pali_word = result
            a.new_id = result.id
            print(a)
            return False
        elif rename_delete == "r":
            print("enter a new name?")
            new_name = input()
            a.pali_word.lemma_1 = new_name
            return test_pali(db_session, a)
    else:
        print(a)
        db_session.add(a.pali_word)
        return True


if __name__ == "__main__":
    main()
    # additions_list = Addition.load_additions()
    # print(additions_list)