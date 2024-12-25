#!/usr/bin/env python3

"""Move all examples to lower position if the position is empty"""
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).all()

    with db_session.no_autoflush:
        for i in db:
            if i.sbs:
                # Gather all example fields into a list
                sbs_example_fields = [
                    i.sbs.sbs_example_1,
                    i.sbs.sbs_example_2,
                    i.sbs.sbs_example_3,
                    i.sbs.sbs_example_4
                ]

                # Collect non-empty examples
                non_empty_examples = []
                for idx, val in enumerate(sbs_example_fields):
                    if val:
                        non_empty_examples.append((val, idx + 1))  # (value, original position)

                # If there is any empty space before the filled ones, move them
                if len(non_empty_examples) < len(sbs_example_fields):
                    # print(f"Reordering fields for Word ID: {i.id}")
                    target_position = 1

                    # Move non-empty examples to the start
                    for val, current_position in non_empty_examples:
                        for field_prefix in ['sbs_source', 'sbs_sutta', 'sbs_example', 'sbs_chant_pali', 'sbs_chant_eng', 'sbs_chapter']:
                            # Move value from current_position to target_position
                            value = getattr(i.sbs, f"{field_prefix}_{current_position}")
                            setattr(i.sbs, f"{field_prefix}_{target_position}", value)
                            
                        # Increment target_position after filling
                        target_position += 1

                    # Clear the remaining fields
                    for pos in range(target_position, 5):  # Assuming there are 4 positions
                        for field_prefix in ['sbs_source', 'sbs_sutta', 'sbs_example', 'sbs_chant_pali', 'sbs_chant_eng', 'sbs_chapter']:
                            field_name = f"{field_prefix}_{pos}"
                            setattr(i.sbs, field_name, "")  # Clear field
                    # print(f"Reordering applied for Word ID: {i.id}")

        # Commit after processing all records
        db_session.commit()
        print("All changes committed.")


if __name__ == "__main__":
    main()






