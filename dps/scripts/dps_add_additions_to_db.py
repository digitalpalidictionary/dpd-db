#!/usr/bin/env python3

"""Add new additions to the database without update additions tsv. Keeping same id as in additions.tsv file"""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import p_title
from tools.tsv_read_write import read_tsv_dot_dict


def add_to_db_keeping_id():

    p_title("add additions to db keeping id")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    add_to_db = []
    
    additions_list = read_tsv_dot_dict(pth.additions_tsv_path)
    column_exceptions = [
        "date_created", "name", "comment", "added_to_db",
        "date_added_to_db", "new_id"
        ]
    added_count = 0
    
    for a in additions_list:
        if not a.added_to_db:

            # make new headword
            hw = DpdHeadword()
            hw.id = a.id
            hw.ebt_count = 0    # this needs to happen automatically!

            for column in a:
                if (
                    column not in column_exceptions
                    and hasattr(hw, column)
                ):
                    setattr(hw, column, a[column])
            
            add_to_db.append(hw)
            
            added_count += 1     
            
            print(hw)
    
    print(f"{'added_count:':<20}{added_count:>10}")
    
    if added_count > 0:
        db_session.add_all(add_to_db)
        db_session.commit()
        # write_tsv_dot_dict(pth.additions_tsv_path, additions_list)


if __name__ == "__main__":
    add_to_db_keeping_id()