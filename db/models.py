"""Datebase model for use by SQLAlchemy."""
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
from tools.paths import ProjectPaths as PTH

db_session = get_db_session(PTH.dpd_db_path)


class Base(DeclarativeBase):
    pass


class InflectionTemplates(Base):
    __tablename__ = "inflection_templates"

    pattern: Mapped[str] = mapped_column(primary_key=True)
    like: Mapped[Optional[str]] = mapped_column(default='')
    data: Mapped[Optional[str]] = mapped_column(default='')

    def __repr__(self) -> str:
        return f"InflectionTemplates: {self.pattern} {self.like} {self.data}"


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
    root_info: Mapped[Optional[str]] = mapped_column(default='')
    root_matrix: Mapped[Optional[str]] = mapped_column(default='')
    # ru_root_meaning: Mapped[Optional[str]] = mapped_column(default='')
    # ru_sk_root_meaning: Mapped[Optional[str]] = mapped_column(default='')

    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())

    pw: Mapped[List["PaliWord"]] = relationship(
        back_populates="rt")

    @property
    def root_clean(self) -> str:
        return re.sub(r" \d.*$", "", self.root)

    @property
    def root_no_sign(self) -> str:
        return re.sub(r"\d| |√", "", self.root)

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
        ForeignKey("pali_roots.root"), default='')
    root_sign: Mapped[Optional[str]] = mapped_column(default='')
    root_base: Mapped[Optional[str]] = mapped_column(default='')

    family_root: Mapped[Optional[str]] = mapped_column(default='')
    # ForeignKey("family_root.root_family"))
    family_word: Mapped[Optional[str]] = mapped_column(
        ForeignKey("family_word.word_family"), default='')
    family_compound: Mapped[Optional[str]] = mapped_column(default='')
    family_set: Mapped[Optional[str]] = mapped_column(
        ForeignKey("family_set.set"), default='')

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
    pattern: Mapped[Optional[str]] = mapped_column(
        ForeignKey("inflection_templates.pattern"), default='')

    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())

    rt: Mapped[PaliRoot] = relationship(uselist=False)

    dd = relationship("DerivedData", uselist=False)

    sbs = relationship("SBS", uselist=False)

    ru = relationship("Russian", uselist=False)

    it: Mapped[InflectionTemplates] = relationship()

    @property
    def pali_1_(self) -> str:
        return self.pali_1.replace(" ", "_").replace(".", "_")

    @property
    def pali_link(self) -> str:
        return self.pali_1.replace(" ", "%20")

    @property
    def pali_clean(self) -> str:
        return re.sub(r" \d.*$", "", self.pali_1)

    @property
    def root_clean(self) -> str:
        try:
            return re.sub(r" \d.*$", "", self.root_key)
        except Exception as e:
            print(f"{self.pali_1}: {e}")

    @property
    def family_compound_list(self) -> list:
        if self.family_compound:
            return self.family_compound.split(" ")
        else:
            return [self.family_compound]

    @property
    def family_set_list(self) -> list:
        if self.family_set:
            return self.family_set.split("; ")
        else:
            return [self.family_set]

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

    @property
    def synonym_list(self) -> list:
        if self.synonym:
            return self.synonym.split(", ")
        else:
            return [self.synonym]

    @property
    def variant_list(self) -> list:
        if self.variant:
            return self.variant.split(", ")
        else:
            return [self.variant]

    def __repr__(self) -> str:
        return f"""PaliWord: {self.id} {self.pali_1} {self.pos} {
            self.meaning_1}"""


class DerivedData(Base):
    __tablename__ = "derived_data"

    id: Mapped[int] = mapped_column(
        ForeignKey('pali_words.id'), primary_key=True)
    # pali_1: Mapped[str] = mapped_column(unique=True)
    inflections: Mapped[Optional[str]] = mapped_column(default='')
    sinhala: Mapped[Optional[str]] = mapped_column(default='')
    devanagari: Mapped[Optional[str]] = mapped_column(default='')
    thai: Mapped[Optional[str]] = mapped_column(default='')
    html_table: Mapped[Optional[str]] = mapped_column(default='')
    freq_html: Mapped[Optional[str]] = mapped_column(default='')

    @property
    def inflections_list(self) -> list:
        return self.inflections.split(",")

    @property
    def sinhala_list(self) -> list:
        return self.sinhala.split(",")

    @property
    def devanagari_list(self) -> list:
        return self.devanagari.split(",")

    @property
    def thai_list(self) -> list:
        return self.thai.split(",")

    def __repr__(self) -> str:
        return f"DerivedData: {self.id} {PaliWord.pali_1} {self.inflections}"


class Sandhi(Base):
    __tablename__ = "sandhi"
    id: Mapped[int] = mapped_column(primary_key=True)
    sandhi: Mapped[str] = mapped_column(unique=True)
    split: Mapped[str] = mapped_column(default='')
    sinhala: Mapped[Optional[str]] = mapped_column(default='')
    devanagari: Mapped[Optional[str]] = mapped_column(default='')
    thai: Mapped[Optional[str]] = mapped_column(default='')

    @property
    def split_list(self) -> list:
        return self.split.split(",")

    @property
    def sinhala_list(self) -> list:
        return self.sinhala.split(",")

    @property
    def devanagari_list(self) -> list:
        return self.devanagari.split(",")

    @property
    def thai_list(self) -> list:
        return self.thai.split(",")

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
    word_family: Mapped[str] = mapped_column(primary_key=True)
    html: Mapped[str] = mapped_column(default='')
    count: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"FamilyWord: {self.id} {self.word_family} {self.count}"


class FamilySet(Base):
    __tablename__ = "family_set"
    set: Mapped[str] = mapped_column(primary_key=True)
    html: Mapped[str] = mapped_column(default='')
    count: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"FamilySet: {self.id} {self.set} {self.count}"


class SBS(Base):
    __tablename__ = "sbs"

    id: Mapped[int] = mapped_column(
        ForeignKey('pali_words.id'), primary_key=True)
    sbs_class_anki: Mapped[Optional[int]] = mapped_column(default='')
    sbs_class: Mapped[Optional[int]] = mapped_column(default='')
    sbs_meaning: Mapped[Optional[str]] = mapped_column(default='')
    sbs_notes: Mapped[Optional[str]] = mapped_column(default='')
    sbs_source_1: Mapped[Optional[str]] = mapped_column(default='')
    sbs_sutta_1: Mapped[Optional[str]] = mapped_column(default='')
    sbs_example_1: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_pali_1: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_eng_1: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chapter_1: Mapped[Optional[str]] = mapped_column(default='')
    sbs_source_2: Mapped[Optional[str]] = mapped_column(default='')
    sbs_sutta_2: Mapped[Optional[str]] = mapped_column(default='')
    sbs_example_2: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_pali_2: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_eng_2: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chapter_2: Mapped[Optional[str]] = mapped_column(default='')
    sbs_source_3: Mapped[Optional[str]] = mapped_column(default='')
    sbs_sutta_3: Mapped[Optional[str]] = mapped_column(default='')
    sbs_example_3: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_pali_3: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_eng_3: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chapter_3: Mapped[Optional[str]] = mapped_column(default='')
    sbs_source_4: Mapped[Optional[str]] = mapped_column(default='')
    sbs_sutta_4: Mapped[Optional[str]] = mapped_column(default='')
    sbs_example_4: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_pali_4: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chant_eng_4: Mapped[Optional[str]] = mapped_column(default='')
    sbs_chapter_4: Mapped[Optional[str]] = mapped_column(default='')
    sbs_category: Mapped[Optional[str]] = mapped_column(default='')

    def __repr__(self) -> str:
        return f"SBS: {self.id} {self.sbs_chant_pali_1} {self.sbs_class}"


class Russian(Base):
    __tablename__ = "russian"

    id: Mapped[int] = mapped_column(
        ForeignKey('pali_words.id'), primary_key=True)
    ru_meaning: Mapped[str] = mapped_column(default="")
    ru_meaning_lit: Mapped[Optional[str]] = mapped_column(default="")
    ru_notes: Mapped[Optional[str]] = mapped_column(default='')

    def __repr__(self) -> str:
        return f"Russian: {self.id} {self.ru_meaning}"
