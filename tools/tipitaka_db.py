import sys
from typing import Any, cast

from bs4 import BeautifulSoup
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


class DhpA(SameSchemaMixin, Base):
    __tablename__ = "s0502a_att"  # type: ignore


def search_tipitaka(
    class_name: str, search_string: str
) -> tuple[str, str] | tuple[None, None]:
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
        return None, None

    AnyTable = cast(Any, TargetTable)
    query_result = (
        db_session.query(AnyTable)
        .filter(AnyTable.pali_text.contains(search_string))
        .first()
    )

    if query_result:
        any_result = cast(Any, query_result)
        soup = BeautifulSoup(any_result.pali_text, "html.parser")
        pali_text = soup.get_text()
        english_translation = any_result.english_translation
        return pali_text, english_translation
    else:
        return None, None


if __name__ == "__main__":
    pali_text, english_translation = search_tipitaka("DhpA", "katakicc")
    if pali_text and english_translation:
        print(pali_text)
        print()
        print(english_translation)
        print()

# windows server "remina"
