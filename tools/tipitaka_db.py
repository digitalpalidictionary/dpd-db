import sys
from typing import Any, cast

from bs4 import BeautifulSoup
from rich import print
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, declared_attr, sessionmaker


def get_tipitaka_db_session() -> Session:
    """Get the tipitaka db session."""

    db_eng = create_engine(
        "sqlite:///resources/tipitaka_translation_data/tipitaka_translation_data.db",
        echo=False,
    )

    Session = sessionmaker(db_eng)
    Session.configure(bind=db_eng)
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
        # The table name will be the lowercase class name (e.g., Table1 -> table1)
        # You can customize this logic if your table names are different.
        return cls.__name__.lower()  # type: ignore


class dhpa(SameSchemaMixin, Base):
    __tablename__ = "s0502a_att"  # type: ignore


class jaa1(SameSchemaMixin, Base):
    __tablename__ = "s0513a1_att"  # type: ignore


class jaa2(SameSchemaMixin, Base):
    __tablename__ = "s0513a2_att"  # type: ignore


class jaa3(SameSchemaMixin, Base):
    __tablename__ = "s0513a3_att"  # type: ignore


class jaa4(SameSchemaMixin, Base):
    __tablename__ = "s0513a4_att"  # type: ignore


def search_tipitaka(class_name: str, search_string: str) -> list[tuple[str, str]]:
    """
    Search Tipitaka texts for a string and return cleaned pali text and English translation.

    :param class_name: The name of the table class to search.
    :param search_string: The string to search for in pali_text.
    :return: A tuple of (pali_text, english_translation) or (None, None) if not found.
    """
    db_session = get_tipitaka_db_session()

    current_module = sys.modules[__name__]
    TargetTable = getattr(current_module, class_name, None)

    if TargetTable is None or not issubclass(TargetTable, Base):
        return []

    AnyTable = cast(Any, TargetTable)
    query_result = (
        db_session.query(AnyTable)
        .filter(AnyTable.pali_text.contains(search_string))
        .all()
    )

    compiled_results = []
    if query_result:
        for q in query_result:
            soup = BeautifulSoup(q.pali_text, "html.parser")
            pali_text = soup.get_text()
            compiled_results.append((pali_text, q.english_translation))
        return compiled_results
    else:
        return []


def tui_interface():
    user_book = ""
    while user_book != "exit":
        print("[green]what book? dhpa jaa1 jaa2 jaa3 jaa4", end=" ")
        user_book = input()
        print("[green]what word?", end=" ")
        user_word = input()

        compiled_results = search_tipitaka(user_book, user_word)
        for result in compiled_results:
            pali_text, english_translation = result
            pali_text_highlighted = pali_text.replace(
                user_word, f"[white]{user_word}[/white]"
            )
            print()
            print(f"[green]{pali_text_highlighted}")
            print(f"[cyan]{english_translation}")
            print()
        print("-" * 50)
        print()


if __name__ == "__main__":
    tui_interface()
