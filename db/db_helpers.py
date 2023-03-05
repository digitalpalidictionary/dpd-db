from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy_utils import database_exists
from sqlalchemy_utils import create_database
from db.models import Base


def create_db_if_not_exists(db_path: Path):
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.create_all(bind=engine)


def print_column_names(tables_name):

    inspector = inspect(tables_name)
    column_names = [column.name for column in inspector.columns]
    for counter, column_name in enumerate(column_names):
        print(f"{counter}. {column_name}")
