#!/usr/bin/env python3

"""Convert /r/n to /n."""

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from db.db_helpers import get_column_names
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    columns = get_column_names(DpdHeadwords)
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
