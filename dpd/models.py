from typing import List
from typing import Optional

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class PaliRoot(Base):
    __tablename__ = "pali_roots"

    root: Mapped[str] = mapped_column(primary_key=True)

    # root_counter: Mapped[Optional[int]]

    root_in_comps:         Mapped[Optional[str]]
    root_has_verb:         Mapped[Optional[str]]
    root_group:            Mapped[Optional[int]]
    root_sign:             Mapped[Optional[str]]
    root_base:             Mapped[Optional[str]]
    root_meaning:          Mapped[Optional[str]]
    sanskrit_root:         Mapped[Optional[str]]
    sanskrit_root_meaning: Mapped[Optional[str]]
    sanskrit_root_class:   Mapped[Optional[str]]
    root_example:          Mapped[Optional[str]]
    dhatupatha_num:        Mapped[Optional[str]]
    dhatupatha_root:       Mapped[Optional[str]]
    dhatupatha_pali:       Mapped[Optional[str]]
    dhatupatha_english:    Mapped[Optional[str]]
    dhatumanjusa_num:      Mapped[Optional[int]]
    dhatumanjusa_root:     Mapped[Optional[str]]
    dhatumanjusa_pali:     Mapped[Optional[str]]
    dhatumanjusa_english:  Mapped[Optional[str]]
    dhatumala_root:        Mapped[Optional[str]]
    dhatumala_pali:        Mapped[Optional[str]]
    dhatumala_english:     Mapped[Optional[str]]
    panini_root:           Mapped[Optional[str]]
    panini_sanskrit:       Mapped[Optional[str]]
    panini_english:        Mapped[Optional[str]]
    note:                  Mapped[Optional[str]]
    matrix_test:           Mapped[Optional[str]]

    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    pali_words: Mapped[List["PaliWord"]] = relationship(back_populates="pali_root")

    def __repr__(self) -> str:
        return f"""
PaliRoot(
    root = {self.root},
    root_in_comps = {self.root_in_comps},
    root_base = {self.root_base},
    root_meaning = {self.root_meaning},
...etc.)""".strip()


class PaliWord(Base):
    __tablename__ = "pali_words"

    id: Mapped[int] = mapped_column(primary_key=True)

    pali_1: Mapped[str] = mapped_column(unique=True)

    pali_2:                Mapped[Optional[str]]
    pos:                   Mapped[Optional[str]]
    grammar:               Mapped[Optional[str]]
    derived_from:          Mapped[Optional[str]]
    neg:                   Mapped[Optional[str]]
    verb:                  Mapped[Optional[str]]
    trans:                 Mapped[Optional[str]]
    plus_case:             Mapped[Optional[str]]

    meaning_1:             Mapped[Optional[str]]
    meaning_2:             Mapped[Optional[str]]
    meaning_lit:           Mapped[Optional[str]]

    non_ia:                Mapped[Optional[str]]
    sanskrit:              Mapped[Optional[str]]
    root_sign:             Mapped[Optional[str]]
    base:                  Mapped[Optional[str]]
    family_root:           Mapped[Optional[str]]
    family_word:           Mapped[Optional[str]]
    family_compound:       Mapped[Optional[str]]
    construction:          Mapped[Optional[str]]
    derivative:            Mapped[Optional[str]]
    suffix:                Mapped[Optional[str]]
    phonetic:              Mapped[Optional[str]]
    compound_type:         Mapped[Optional[str]]
    compound_construction: Mapped[Optional[str]]
    non_root_in_comps:     Mapped[Optional[str]]

    source_1:              Mapped[Optional[str]]
    sutta_1:               Mapped[Optional[str]]
    example_1:             Mapped[Optional[str]]

    source_2:              Mapped[Optional[str]]
    sutta_2:               Mapped[Optional[str]]
    example_2:             Mapped[Optional[str]]

    antonym:               Mapped[Optional[str]]
    synonym:               Mapped[Optional[str]]
    variant:               Mapped[Optional[str]]
    commentary:            Mapped[Optional[str]]
    notes:                 Mapped[Optional[str]]
    cognate:               Mapped[Optional[str]]
    category:              Mapped[Optional[str]]
    link:                  Mapped[Optional[str]]
    stem:                  Mapped[Optional[str]]
    pattern:               Mapped[Optional[str]]

    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    root_key: Mapped[Optional[str]] = mapped_column(ForeignKey("pali_roots.root"))

    pali_root: Mapped[PaliRoot] = relationship(back_populates="pali_words", uselist=False)

    def __repr__(self) -> str:
        return f"""
PaliWord(
    pali_1 = {self.pali_1},
    meaning_1 = {self.meaning_1},
...etc.)""".strip()
