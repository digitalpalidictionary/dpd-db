#!/usr/bin/env python3

"""Add new additions to the database and update additions tsv."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.date_and_time import year_month_day_dash
from tools.paths import ProjectPaths
from tools.printer import p_title
from tools.tsv_read_write import read_tsv_dot_dict, write_tsv_dot_dict


def add_to_db():

    p_title("add additions to db")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    add_to_db = []
    
    last_id = max(db_session.query(DpdHeadword.id).all())[0]
    next_id = last_id + 1
    print(f"{'last_id:':<20}{last_id:>10}")
    print(f"{'next_id:':<20}{next_id:>10}")

    additions_list = read_tsv_dot_dict(pth.additions_tsv_path)
    column_exceptions = [
        "date_created", "name", "comment", "added_to_db",
        "date_added_to_db", "new_id", "id"
        ]
    added_count = 0
    date = year_month_day_dash()
    
    for a in additions_list:
        if not a.added_to_db:

            # make new headword
            hw = DpdHeadword()
            hw.id = next_id
            hw.ebt_count = 0    # this needs to happen automatically!

            for column in a:
                if (
                    column not in column_exceptions
                    and hasattr(hw, column)
                ):
                    setattr(hw, column, a[column])
            
            add_to_db.append(hw)
            
            # update additions
            a.added_to_db = "yes"
            a.date_added_to_db = date
            a.new_id = next_id

            # increment
            next_id = next_id + 1
            added_count += 1     
            
            print(hw)
    
    print(f"{'added_count:':<20}{added_count:>10}")
    
    if added_count > 0:
        db_session.add_all(add_to_db)
        db_session.commit()
        write_tsv_dot_dict(pth.additions_tsv_path, additions_list)


if __name__ == "__main__":
    add_to_db()