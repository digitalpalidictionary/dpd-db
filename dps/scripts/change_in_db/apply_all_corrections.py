#!/usr/bin/env python3

"""apply all from corrections.tsv."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def load_corrections_tsv():
    file_path = pth.corrections_tsv_path
    corrections_list = read_tsv_dot_dict(file_path)
    return corrections_list


def apply_all_suggestions():

    corrections_list = load_corrections_tsv()

    added_lines_count = 0

    for correction in corrections_list:
        if not correction.approved:
            db = db_session.query(DpdHeadword).filter(
                correction.id == DpdHeadword.id).first()
            if db:
                id = correction.id
                field1 = correction.field1
                field2 = correction.field2
                field3 = correction.field3
                value1 = correction.value1
                value2 = correction.value2
                value3 = correction.value3

                if field1 and value1 is not None:
                    setattr(db, field1, value1)
                    added_lines_count += 1
                    print(f"{added_lines_count} {id}: {field1} with {value1}")
                if field2 and value2 is not None:
                    setattr(db, field2, value2)
                    added_lines_count += 1
                    print(f"{added_lines_count} {id}: {field2} with {value2}")
                if field3 and value3 is not None:
                    setattr(db, field3, value3)
                    added_lines_count += 1
                    print(f"{added_lines_count} {id}: {field3} with {value3}")
                
                db_session.commit()
            else:
                print(f"Entry with ID {correction.id} not found.")

    print(f"Total number of applied corrections: {added_lines_count}")


apply_all_suggestions()
