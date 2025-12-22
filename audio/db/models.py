"""Database models for DPD audio files."""

from enum import Enum
from typing import Optional

from sqlalchemy import LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Gender(Enum):
    """Enum for audio gender variants."""

    MALE = "male"
    FEMALE = "female"


class DpdAudio(Base):
    """Audio files database model for DPD pronunciations."""

    __tablename__ = "dpd_audio"

    # Primary key using lemma_clean (matches the lemma_clean field from dpd_headwords)
    lemma_clean: Mapped[str] = mapped_column(primary_key=True, index=True)

    # Audio file blobs for male and female voices
    male1: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    male2: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    female1: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    def __repr__(self) -> str:
        return f"<DpdAudio(lemma_clean='{self.lemma_clean}')>"
