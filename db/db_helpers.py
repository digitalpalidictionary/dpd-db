from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy_utils import database_exists
from db.models import Base


def create_db_if_not_exists(db_path: Path):
    """Create the db if it does not exist already."""
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
    if not database_exists(engine.url):
        Base.metadata.create_all(bind=engine)


def print_column_names(tables_name):
    """Print a numbered list of all the column names in a given table."""

    inspector = inspect(tables_name)
    column_names = [column.name for column in inspector.columns]
    for counter, column_name in enumerate(column_names):
        print(f"{counter}. {column_name}")
