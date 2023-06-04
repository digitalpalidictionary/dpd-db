#!/usr/bin/env python3.11

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.meaning_construction import summarize_constr


def main():
    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(PaliWord).all()
    x = summarize_constr(dpd_db)
    print(x)


if __name__ == "__main__":
    main()
