"""Manager for speech marks (apostrophes and hyphens)."""

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import load_only
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.clean_sentence import split_pali_sentence_into_words
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths

SpeechMarksDict = dict[str, list[str]]


class SpeechMarkManager:
    def __init__(self, paths: ProjectPaths | None = None):
        if paths is None:
            self.pth = ProjectPaths()
        else:
            self.pth = paths

        self.speech_marks_dict: SpeechMarksDict = {}
        self._load_data()

    def _load_data(self):
        # Load from unified JSON if it exists
        if self.pth.speech_marks_path.exists():
            with open(self.pth.speech_marks_path, "r", encoding="utf-8") as f:
                self.speech_marks_dict = json.load(f)

    def get_speech_marks(self) -> SpeechMarksDict:
        return self.speech_marks_dict

    def get_variants(self, clean_word: str) -> list[str] | None:
        return self.speech_marks_dict.get(clean_word)

    def has_variants(self, clean_word: str) -> bool:
        return clean_word in self.speech_marks_dict

    def update_variants(self, clean_word: str, variant: str):
        if clean_word not in self.speech_marks_dict:
            self.speech_marks_dict[clean_word] = [variant]
        elif variant not in self.speech_marks_dict[clean_word]:
            self.speech_marks_dict[clean_word].append(variant)

    def save(self):
        """Save in Pāḷi sort order (keys and variants) for stable git diffs."""
        sorted_dict = {
            key: sorted(self.speech_marks_dict[key], key=pali_sort_key)
            for key in sorted(self.speech_marks_dict, key=pali_sort_key)
        }
        with open(self.pth.speech_marks_path, "w", encoding="utf-8") as f:
            json.dump(sorted_dict, f, ensure_ascii=False, indent=2)

    def _should_regenerate(self) -> bool:
        """Check if cache is older than 1 day"""
        return (
            not self.pth.speech_marks_path.exists()
            or datetime.now()
            - datetime.fromtimestamp(self.pth.speech_marks_path.stat().st_mtime)
            > timedelta(days=1)
        )

    def regenerate_from_db(self):
        """Rebuild the speech marks dict from scratch from db text.

        The db is the single source of truth: every word containing an
        apostrophe or hyphen in example_1, example_2 or commentary is
        collected, keyed by its clean form (both marks stripped) — the
        same convention as gui2's live capture. A second pass adds the
        plain unmarked word as a variant wherever it also occurs in the
        corpus, so genuinely ambiguous words keep both possibilities.
        Entries no longer backed by db text disappear on rebuild.
        """
        db_session: Session = get_db_session(self.pth.dpd_db_path)
        db = (
            db_session.query(DpdHeadword)
            .options(
                load_only(
                    DpdHeadword.example_1,
                    DpdHeadword.example_2,
                    DpdHeadword.commentary,
                )
            )
            .all()
        )

        self.speech_marks_dict = {}
        for i in db:
            for field in (i.example_1, i.example_2, i.commentary):
                if field and ("'" in field or "-" in field):
                    for word in split_pali_sentence_into_words(field):
                        if "'" in word or "-" in word:
                            clean_word = word.replace("-", "").replace("'", "")
                            if clean_word:
                                self.update_variants(clean_word, word)

        for i in db:
            for field in (i.example_1, i.example_2, i.commentary):
                if field:
                    for word in split_pali_sentence_into_words(field):
                        if word in self.speech_marks_dict:
                            self.update_variants(word, word)

        db_session.close()
        self.save()
