import re
from typing import Any, cast

from bs4 import BeautifulSoup
from rich import print
from rich.progress import track
from sqlalchemy import Column, Integer, String, create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, declared_attr, sessionmaker

from tools.pali_text_files import cst_texts


@event.listens_for(Engine, "connect")
def sqlite_engine_connect(dbapi_connection, connection_record):
    """Enable case-insensitive REGEXP for SQLite connections."""

    def regexp(expr, item):
        if item is None:
            return False
        reg = re.compile(expr, re.IGNORECASE)
        return reg.search(item) is not None

    dbapi_connection.create_function("REGEXP", 2, regexp)


def get_db_engine():
    """Gets the SQLAlchemy engine for the Tipitaka DB."""
    return create_engine(
        "sqlite:///resources/tipitaka_translation_data/tipitaka_translation_data.db",
        echo=False,
    )


def get_tipitaka_db_session() -> Session:
    """Get the tipitaka db session."""
    db_eng = get_db_engine()
    Session = sessionmaker(bind=db_eng)
    db_session = Session()
    return db_session


class Base(DeclarativeBase):
    pass


class SameSchemaMixin:
    """Mixin for tables with identical columns."""

    id = Column(Integer, primary_key=True)
    rend = Column(String)
    paranum = Column(String)
    pali_text = Column(String)
    myanmar_pali_text = Column(String)
    chinese_translation = Column(String)
    chinese_translation_mark = Column(String)
    chinese_translation_timestamp = Column(String)
    english_translation = Column(String)
    english_translation_mark = Column(String)
    english_translation_timestamp = Column(String)

    @declared_attr
    def __tablename__(cls):
        # This is a fallback and will be overridden by dynamic class creation
        return cls.__name__.lower()  # type: ignore


_class_cache = {}


def get_table_class(table_name: str) -> type:
    """Dynamically create and cache a SQLAlchemy table class."""
    if table_name in _class_cache:
        return _class_cache[table_name]

    # Create a valid Python class name from the table name
    class_name = "Table_" + "".join(c for c in table_name.title() if c.isalnum())

    table_class = type(
        class_name, (SameSchemaMixin, Base), {"__tablename__": table_name}
    )
    _class_cache[table_name] = table_class
    return table_class


def get_table_names_for_book(book_name: str) -> list[str]:
    """Get table names for a book from cst_texts."""
    filenames = cst_texts.get(book_name, [])
    table_names = [
        filename[:-4].replace(".", "_")
        for filename in filenames
        if filename.endswith(".txt")
    ]
    return table_names


def search_tipitaka(table_name: str, search_string: str) -> list[tuple[str, str, str]]:
    """
    Search a single Tipitaka table for a string and return cleaned pali text and English translation.

    :param table_name: The name of the table to search.
    :param search_string: The string to search for in pali_text.
    :return: A list of tuples (pali_text, english_translation, table_name).
    """
    db_session = get_tipitaka_db_session()

    try:
        TargetTable = get_table_class(table_name)
    except Exception:
        # This error is unlikely with the current implementation
        return []

    AnyTable = cast(Any, TargetTable)

    try:
        query_result = (
            db_session.query(AnyTable)
            .filter(AnyTable.pali_text.op("REGEXP")(search_string))
            .all()
        )
    except Exception:
        # This can happen if the table doesn't exist in the db, which is expected
        # for some filenames in cst_texts. Suppress error printing.
        return []

    compiled_results = []
    if query_result:
        for q in query_result:
            soup = BeautifulSoup(q.pali_text, "html.parser")
            pali_text = soup.get_text()
            compiled_results.append((pali_text, q.english_translation, table_name))
    return compiled_results


def search_book(book_name: str, search_string: str) -> list[tuple[str, str, str, str]]:
    """Search all tables related to a book."""
    table_names = get_table_names_for_book(book_name)
    if not table_names:
        return []

    all_results = []
    for table_name in table_names:
        results = search_tipitaka(table_name, search_string)
        for pali, eng, table in results:
            all_results.append((pali, eng, table, book_name))
    return all_results


def search_all_cst_texts(search_string: str) -> list[tuple[str, str, str, str]]:
    """Search all tables derived from cst_texts, in the order they appear."""
    all_results = []
    for book_name in track(cst_texts.keys(), description="Searching all books..."):
        results = search_book(book_name, search_string)
        all_results.extend(results)
    return all_results


def get_all_db_table_names():
    """Gets all table names from the database."""
    engine = get_db_engine()
    inspector = inspect(engine)
    return set(inspector.get_table_names())


def get_all_cst_table_names():
    """Gets all table names derived from the cst_texts dictionary."""
    all_table_names = set()
    for book_name in cst_texts.keys():
        table_names = get_table_names_for_book(book_name)
        for table_name in table_names:
            all_table_names.add(table_name)
    return all_table_names


def compare_db_and_cst_tables():
    """Compares tables in the DB with tables derived from cst_texts."""
    print("Comparing database tables with cst_texts dictionary...")

    db_tables = get_all_db_table_names()
    cst_tables = get_all_cst_table_names()

    print(f"\nFound {len(db_tables)} tables in the database.")
    print(f"Found {len(cst_tables)} tables derived from cst_texts.")

    db_only_tables = sorted(list(db_tables - cst_tables))
    cst_only_tables = sorted(list(cst_tables - db_tables))

    print("\n" + "=" * 40)
    if db_only_tables:
        print(
            f"[yellow]Tables in the database but NOT in cst_texts ({len(db_only_tables)}):[/yellow]"
        )
        for table in db_only_tables:
            print(f"- {table}")
    else:
        print("[green]All tables in the database are represented in cst_texts.[/green]")

    print("\n" + "=" * 40)
    if cst_only_tables:
        print(
            f"[yellow]Tables in cst_texts but NOT in the database ({len(cst_only_tables)}):[/yellow]"
        )
        for table in cst_only_tables:
            print(f"- {table}")
    else:
        print("[green]All tables derived from cst_texts exist in the database.[/green]")
    print("\n" + "=" * 40)


def tui_interface():
    user_input = ""
    while user_input != "exit":
        print("[green]what book? (e.g. kn14), 'all', or 'exit'", end=" ")
        user_input = input()

        if user_input == "exit":
            break

        print("[green]what word?", end=" ")
        user_word = input()

        if not user_word:
            print("[yellow]Please enter a word to search.")
            continue

        compiled_results = []
        if user_input == "all":
            compiled_results = search_all_cst_texts(user_word)
        elif user_input in cst_texts:
            print(f"Searching in book '{user_input}'...")
            compiled_results = search_book(user_input, user_word)
        else:
            print(f"[red]Book '{user_input}' not found.")
            continue

        if not compiled_results:
            print(f"[yellow]No results found for '{user_word}' in '{user_input}'.")

        print(f"\nFound {len(compiled_results)} results.")
        for result in compiled_results:
            pali_text, english_translation, table_name, book_name = result
            pali_text_highlighted = pali_text.replace(
                user_word, f"[white on black]{user_word}[/white on black]"
            )
            print()
            print(f"[bright_yellow]book: {book_name}")
            print(f"[yellow]table: {table_name}")
            print(f"[green]{pali_text_highlighted}")
            print(f"[cyan]{english_translation}")
            print()
        print("-" * 50)
        print()


if __name__ == "__main__":
    # To compare DB tables with cst_texts, uncomment the line below
    compare_db_and_cst_tables()

    tui_interface()
