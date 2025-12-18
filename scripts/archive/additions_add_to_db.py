"""Add user additions to db, saving the old & new IDs."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword  # PaliWord
from sqlalchemy.orm.session import make_transient

from tools.paths import ProjectPaths
from tools.addition_class import Addition


def main():
    print("[bright_yellow]add additions to db")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # get the very last id number
    last_id = max(db_session.query(DpdHeadword.id).all())[0]
    next_id = last_id + 1
    print(f"{'last_id:':<20}{last_id:>10}")
    print(f"{'next_id:':<20}{next_id:>10}")

    # open the additions pickle file
    additions_list = Addition.load_additions()

    added_count = 0
    for a in additions_list:
        a: Addition
        hw = a.pali_word

        # check if it's added
        if not a.added_to_db:
            # update the id
            hw.id = next_id

            # always use meaning_1
            if not hw.meaning_1:
                hw.meaning_1 = hw.meaning_2
            a.update(next_id)

            if test_pali(db_session, a):
                # increment the id
                next_id = next_id + 1
                added_count += 1

    db_session.commit()
    Addition.save_additions(additions_list)
    print(f"{'added:':<20}{added_count}")


def remap_pali_word_to_dpd_headword(p):
    make_transient(p)

    hw = DpdHeadword()
    hw.id = p.id
    hw.lemma_1 = p.pali_1
    hw.lemma_2 = p.pali_2
    hw.pos = p.pos
    hw.grammar = p.grammar
    hw.derived_from = p.derived_from
    hw.neg = p.neg
    hw.verb = p.verb
    hw.trans = p.trans
    hw.plus_case = p.plus_case
    hw.meaning_1 = p.meaning_1
    hw.meaning_lit = p.meaning_lit
    hw.meaning_2 = p.meaning_2
    hw.non_ia = p.non_ia
    hw.sanskrit = p.sanskrit
    hw.root_key = p.root_key
    hw.root_sign = p.root_sign
    hw.root_base = p.root_base
    hw.family_root = p.family_root
    hw.family_word = p.family_word
    hw.family_compound = p.family_compound
    hw.family_idioms = ""
    hw.family_set = p.family_set
    hw.construction = p.construction
    hw.derivative = p.derivative
    hw.suffix = p.suffix
    hw.phonetic = p.phonetic
    hw.compound_type = p.compound_type
    hw.compound_construction = p.compound_construction
    hw.non_root_in_comps = p.non_root_in_comps
    hw.source_1 = p.source_1
    hw.sutta_1 = p.sutta_1
    hw.example_1 = p.example_1
    hw.source_2 = p.source_2
    hw.sutta_2 = p.sutta_2
    hw.example_2 = p.example_2
    hw.antonym = p.antonym
    hw.synonym = p.synonym
    hw.variant = p.variant
    hw.var_phonetic = ""
    hw.var_text = ""
    hw.commentary = p.commentary
    hw.notes = p.notes
    hw.cognate = p.cognate
    hw.link = p.link
    hw.origin = p.origin
    hw.stem = p.stem
    hw.pattern = p.pattern
    hw.created_at = p.created_at
    hw.updated_at = p.updated_at
    return hw


def test_pali(db_session, a):
    """Test if pali_word is in the db already."""

    lemma_1 = a.pali_word.lemma_1

    result = db_session.query(DpdHeadword).filter_by(lemma_1=lemma_1).first()
    if result:
        print("[red]duplicate lemma_1 found: ", end="")
        print(f"[white]{a.pali_word}")
        print("[white]r[red]ename or [white]d[red]elete? ", end="")
        rename_delete = input()
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
