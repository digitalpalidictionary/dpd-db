#!/usr/bin/env python3.11

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from db.db_helpers import get_column_names


def main():
    db_session = get_db_session("dpd.db")
    db = db_session.query(PaliWord).all()
    columns = get_column_names(PaliWord)
    r_columns = set()
    r_examples = set()
    for i in db:
        for column in columns:
            if column not in ["id", "user_id", "created_at", "updated_at"]:
                if "\r" in getattr(i, column):
                    new = getattr(i, column).replace("\r\n", "\n")
                    setattr(i, column, new)
                    r_columns.update([column])
                    r_examples.update([getattr(i, column)])

    # db_session.commit()

    print(r_columns)
    print(r_examples)




if __name__ == "__main__":
    main()
