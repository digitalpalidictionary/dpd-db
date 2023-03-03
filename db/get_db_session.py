import os
import sys

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def get_db_session(db_path: Path) -> Session:
    if not os.path.isfile(db_path):
        print(f"Database file doesn't exist: {db_path}")
        sys.exit(1)

    try:
        db_eng = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
        # db_conn = db_eng.connect()

        Session = sessionmaker(db_eng)
        Session.configure(bind=db_eng)
        db_sess = Session()

    except Exception as e:
        print(f"Can't connect to database: {e}")
        sys.exit(1)

    return db_sess
