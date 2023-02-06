import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database

from db.models import Base


def create_db_if_not_exists(db_path: Path):
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.create_all(bind=engine)


def get_db_session(db_path: Path) -> Session:
    if not os.path.isfile(db_path):
        print(f"Database file doesn't exist: {db_path}")
        sys.exit(1)

    try:
        db_eng = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
        Session = sessionmaker(db_eng)
        Session.configure(bind=db_eng)
        db_sess = Session()

    except Exception as e:
        print(f"Can't connect to database: {e}")
        sys.exit(1)

    return db_sess
