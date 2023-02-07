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
    root_in_comps: Mapped[Optional[str]] = mapped_column(default='')
    root_has_verb: Mapped[Optional[str]] = mapped_column(default='')
    root_group: Mapped[Optional[int]] = mapped_column(default=0)
    root_sign: Mapped[Optional[str]] = mapped_column(default='')
    root_meaning: Mapped[Optional[str]] = mapped_column(default='')
    sanskrit_root: Mapped[Optional[str]] = mapped_column(default='')
    sanskrit_root_meaning: Mapped[Optional[str]] = mapped_column(default='')
    sanskrit_root_class: Mapped[Optional[str]] = mapped_column(default='')
    root_example: Mapped[Optional[str]] = mapped_column(default='')
    dhatupatha_num: Mapped[Optional[str]] = mapped_column(default='')
    dhatupatha_root: Mapped[Optional[str]] = mapped_column(default='')
    dhatupatha_pali: Mapped[Optional[str]] = mapped_column(default='')
    dhatupatha_english: Mapped[Optional[str]] = mapped_column(default='')
    dhatumanjusa_num: Mapped[Optional[int]] = mapped_column(default=0)
    dhatumanjusa_root: Mapped[Optional[str]] = mapped_column(default='')
    dhatumanjusa_pali: Mapped[Optional[str]] = mapped_column(default='')
    dhatumanjusa_english: Mapped[Optional[str]] = mapped_column(default='')
    dhatumala_root: Mapped[Optional[str]] = mapped_column(default='')
    dhatumala_pali: Mapped[Optional[str]] = mapped_column(default='')
    dhatumala_english: Mapped[Optional[str]] = mapped_column(default='')
    panini_root: Mapped[Optional[str]] = mapped_column(default='')
    panini_sanskrit: Mapped[Optional[str]] = mapped_column(default='')
    panini_english: Mapped[Optional[str]] = mapped_column(default='')
    note: Mapped[Optional[str]] = mapped_column(default='')
    matrix_test: Mapped[Optional[str]] = mapped_column(default='')

    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())

    pali_words: Mapped[List["PaliWord"]] = relationship(
        back_populates="pali_root")

    def __repr__(self) -> str:
        return f"""{self.root} {self.root_group} {self.root_sign} (
            {self.root_meaning})""".strip()


class PaliWord(Base):
    __tablename__ = "pali_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(unique=True)
    pali_1: Mapped[str] = mapped_column(unique=True)
    pali_2: Mapped[Optional[str]] = mapped_column(default='')
    pos: Mapped[str] = mapped_column(default='')
    grammar: Mapped[str] = mapped_column(default='')
    derived_from: Mapped[Optional[str]] = mapped_column(default='')
    neg: Mapped[Optional[str]] = mapped_column(default='')
    verb: Mapped[Optional[str]] = mapped_column(default='')
    trans:  Mapped[Optional[str]] = mapped_column(default='')
    plus_case:  Mapped[Optional[str]] = mapped_column(default='')

    meaning_1: Mapped[Optional[str]] = mapped_column(default='')
    meaning_lit: Mapped[Optional[str]] = mapped_column(default='')
    meaning_2: Mapped[Optional[str]] = mapped_column(default='')

    non_ia: Mapped[Optional[str]] = mapped_column(default='')
    sanskrit: Mapped[Optional[str]] = mapped_column(default='')

    root_key: Mapped[Optional[str]] = mapped_column(
        ForeignKey("pali_roots.root"))
    root_sign: Mapped[Optional[str]] = mapped_column(default='')
    root_base: Mapped[Optional[str]] = mapped_column(default='')

    family_root: Mapped[Optional[str]] = mapped_column(default='')
    family_word: Mapped[Optional[str]] = mapped_column(default='')
    family_compound: Mapped[Optional[str]] = mapped_column(default='')
    construction:  Mapped[Optional[str]] = mapped_column(default='')
    derivative: Mapped[Optional[str]] = mapped_column(default='')
    suffix: Mapped[Optional[str]] = mapped_column(default='')
    phonetic: Mapped[Optional[str]] = mapped_column(default='')
    compound_type: Mapped[Optional[str]] = mapped_column(default='')
    compound_construction: Mapped[Optional[str]] = mapped_column(default='')
    non_root_in_comps: Mapped[Optional[str]] = mapped_column(default='')

    source_1: Mapped[Optional[str]] = mapped_column(default='')
    sutta_1: Mapped[Optional[str]] = mapped_column(default='')
    example_1: Mapped[Optional[str]] = mapped_column(default='')

    source_2: Mapped[Optional[str]] = mapped_column(default='')
    sutta_2: Mapped[Optional[str]] = mapped_column(default='')
    example_2: Mapped[Optional[str]] = mapped_column(default='')

    antonym: Mapped[Optional[str]] = mapped_column(default='')
    synonym: Mapped[Optional[str]] = mapped_column(default='')
    variant: Mapped[Optional[str]] = mapped_column(default='')
    commentary: Mapped[Optional[str]] = mapped_column(default='')
    notes: Mapped[Optional[str]] = mapped_column(default='')
    cognate: Mapped[Optional[str]] = mapped_column(default='')
    category: Mapped[Optional[str]] = mapped_column(default='')
    link: Mapped[Optional[str]] = mapped_column(default='')

    stem: Mapped[str] = mapped_column(default='')
    pattern: Mapped[Optional[str]] = mapped_column(default='')

    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())

    pali_root: Mapped[PaliRoot] = relationship(
        back_populates="pali_words", uselist=False)

    def __repr__(self) -> str:
        return f"""PaliWord: {self.id} {self.pali_1} {self.pos} {
            self.meaning_1}"""


class InflectionTemplates(Base):
    __tablename__ = "inflection_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    pattern: Mapped[str] = mapped_column(unique=True)
    like: Mapped[Optional[str]] = mapped_column(default='')
    data: Mapped[Optional[str]] = mapped_column(default='')

    def __repr__(self) -> str:
        return f"inflection_templates: {self.pattern} {self.like} {self.data}"


class DerivedInflections(Base):
    __tablename__ = "derived_inflections"

    id: Mapped[int] = mapped_column(primary_key=True)
    pali_1: Mapped[str] = mapped_column(unique=True)
    inflections: Mapped[Optional[str]] = mapped_column(default='')
    sinhala: Mapped[Optional[str]] = mapped_column(default='')
    devanagari: Mapped[Optional[str]] = mapped_column(default='')
    thai: Mapped[Optional[str]] = mapped_column(default='')
    html_table: Mapped[Optional[str]] = mapped_column(default='')
