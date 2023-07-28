#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord


def main():
    db_session = get_db_session("dpd.db")
    db = db_session.query(PaliWord).all()
    for counter, i in enumerate(db):
        print(counter, i.pali_1)


if __name__ == "__main__":
    main()
