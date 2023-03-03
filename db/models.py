import re

from typing import List
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from db.get_db_session import get_db_session
from tools.pali_sort_key import pali_sort_key

db_session = get_db_session("dpd.db")


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

    @property
    def root_clean(self) -> str:
        return re.sub(r" \d.*$", "", self.root)

    @property
    def root_(self) -> str:
        return self.root.replace(" ", "_")

    @property
    def root_link(self) -> str:
        return self.root.replace(" ", "%20")

    @property
    def root_count(self) -> int:
        return db_session.query(
            PaliWord
            ).filter(
                PaliWord.root_key == self.root
            ).count()

    @property
    def root_family_list(self) -> list:
        results = db_session.query(
            PaliWord
        ).filter(
            PaliWord.root_key == self.root
        ).group_by(
            PaliWord.family_root
        ).all()
        family_list = [i.family_root for i in results]
        family_list = sorted(family_list, key=pali_sort_key)
        return family_list

    def __repr__(self) -> str:
        return f"""PaliRoot: {self.root} {self.root_group} {self.root_sign} ({self.root_meaning})"""


class PaliWord(Base):
    __tablename__ = "pali_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        unique=True)
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
    family_set: Mapped[Optional[str]] = mapped_column(default='')

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
    link: Mapped[Optional[str]] = mapped_column(default='')
    origin: Mapped[Optional[str]] = mapped_column(default='')

    stem: Mapped[str] = mapped_column(default='')
    pattern: Mapped[Optional[str]] = mapped_column(default='')

    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())

    pali_root: Mapped[PaliRoot] = relationship(
        back_populates="pali_words", uselist=False)

    @property
    def pali_1_(self) -> str:
        return self.pali_1.replace(" ", "_").replace(".", "_")

    @property
    def pali_clean(self) -> str:
        return re.sub(r" \d.*$", "", self.pali_1)

    @property
    def root_clean(self) -> str:
        return re.sub(r" \d.*$", "", self.root_key)

    @property
    def family_compound_list(self) -> list:
        if self.family_compound:
            return self.family_compound.split(" ")
        else:
            return [self.family_compound]

    @property
    def root_count(self) -> int:
        return db_session.query(
            PaliWord.id
        ).filter(
            PaliWord.root_key == self.root_key
        ).count()

    @property
    def pos_list(self) -> list:
        pos_db = db_session.query(
            PaliWord.pos
        ).group_by(
            PaliWord.pos
        ).all()
        return sorted([i.pos for i in pos_db])

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
        return f"InflectionTemplates: {self.pattern} {self.like} {self.data}"


class DerivedData(Base):
    __tablename__ = "derived_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    pali_1: Mapped[str] = mapped_column(unique=True)
    inflections: Mapped[Optional[str]] = mapped_column(default='')
    sinhala: Mapped[Optional[str]] = mapped_column(default='')
    devanagari: Mapped[Optional[str]] = mapped_column(default='')
    thai: Mapped[Optional[str]] = mapped_column(default='')
    html_table: Mapped[Optional[str]] = mapped_column(default='')
    freq_data: Mapped[Optional[str]] = mapped_column(default='')
    freq_html: Mapped[Optional[str]] = mapped_column(default='')

    def __repr__(self) -> str:
        return f"DerivedData: {self.id} {self.pali_1} {self.inflections}"


class Sandhi(Base):
    __tablename__ = "sandhi"
    id: Mapped[int] = mapped_column(primary_key=True)
    sandhi: Mapped[str] = mapped_column(unique=True)
    split: Mapped[str] = mapped_column(default='')
    sinhala: Mapped[Optional[str]] = mapped_column(default='')
    devanagari: Mapped[Optional[str]] = mapped_column(default='')
    thai: Mapped[Optional[str]] = mapped_column(default='')

    def __repr__(self) -> str:
        return f"Sandhi: {self.id} {self.sandhi} {self.split}"


class FamilyRoot(Base):
    __tablename__ = "family_root"
    id: Mapped[int] = mapped_column(primary_key=True)
    root_id: Mapped[str] = mapped_column(default='')
    root_family: Mapped[str] = mapped_column(default='')
    html: Mapped[str] = mapped_column(default='')
    count: Mapped[int] = mapped_column(default=0)

    @property
    def root_family_link(self) -> str:
        return self.root_family.replace(" ", "%20")

    @property
    def root_family_(self) -> str:
        return self.root_family.replace(" ", "_")

    def __repr__(self) -> str:
        return f"FamilyRoot: {self.id} {self.root_id} {self.root_family} {self.count}"


class FamilyCompound(Base):
    __tablename__ = "family_compound"
    id: Mapped[int] = mapped_column(primary_key=True)
    compound_family: Mapped[str] = mapped_column(unique=True)
    html: Mapped[str] = mapped_column(default='')
    count: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"FamilyCompound: {self.id} {self.compound_family} {self.count}"


class FamilyWord(Base):
    __tablename__ = "family_word"
    id: Mapped[int] = mapped_column(primary_key=True)
    word_family: Mapped[str] = mapped_column(unique=True)
    html: Mapped[str] = mapped_column(default='')
    count: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"FamilyWord: {self.id} {self.word_family} {self.count}"


class FamilySet(Base):
    __tablename__ = "family_set"
    id: Mapped[int] = mapped_column(primary_key=True)
    set: Mapped[str] = mapped_column(unique=True)
    html: Mapped[str] = mapped_column(default='')
    count: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"FamilySet: {self.id} {self.set} {self.count}"
