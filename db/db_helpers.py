"""DB related functions:
1. Create db if doesn't already exist,
2. Create db Session
3. Get column names,
4. Print column names.
"""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base
from tools.printer import printer as pr


def create_db_if_not_exists(db_path: Path):
    """Create the db if it does not exist already."""
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
    if not db_path.is_file():
        Base.metadata.create_all(bind=engine)


def get_db_session(db_path: Path) -> Session:
    """Get the db session, used ubiquitously."""
    if not os.path.isfile(db_path):
        pr.red(f"Database file doesn't exist: {db_path}")
        sys.exit(1)

    try:
        db_eng = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
        # db_conn = db_eng.connect()

        Session = sessionmaker(db_eng)
        Session.configure(bind=db_eng)
        db_sess = Session()

    except Exception as e:
        pr.red(f"Can't connect to database: {e}")
        sys.exit(1)

    return db_sess


def print_column_names(tables_name):
    """Print a numbered list of all the column names in a given table."""

    inspector = inspect(tables_name)
    column_names = [column.name for column in inspector.columns]
    for counter, column_name in enumerate(column_names):
        print(f"{counter}. {column_name}")


def get_column_names(tables_name):
    inspector = inspect(tables_name)
    column_names = [column.name for column in inspector.columns]
    return column_names
