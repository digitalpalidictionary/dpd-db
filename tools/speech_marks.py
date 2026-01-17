"""Manager for speech marks (apostrophes and hyphens)."""

import json
from datetime import datetime, timedelta
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

SpeechMarksDict = dict[str, list[str]]


class SpeechMarkManager:
    def __init__(self, paths: ProjectPaths | None = None):
        if paths is None:
            self.pth = ProjectPaths()
        else:
            self.pth = paths

        self.speech_marks_dict: SpeechMarksDict = {}
        self._exceptions: list[str] = [
            "maññeti",
            "āyataggaṃ",
            "nayanti",
            "āṇāti",
            "gacchanti",
            "jīvanti",
            "sayissanti",
            "gāmeti",
        ]
        self._load_data()

    def _load_data(self):
        # Load from unified JSON if it exists
        if self.pth.speech_marks_path.exists():
            with open(self.pth.speech_marks_path, "r", encoding="utf-8") as f:
                self.speech_marks_dict = json.load(f)

        # Load and merge old hyphenations for migration period
        if self.pth.hyphenations_dict_path.exists():
            with open(self.pth.hyphenations_dict_path, "r", encoding="utf-8") as f:
                old_hyphenations: dict[str, str] = json.load(f)
                for clean_word, variant in old_hyphenations.items():
                    if clean_word not in self.speech_marks_dict:
                        self.speech_marks_dict[clean_word] = [variant]
                    elif variant not in self.speech_marks_dict[clean_word]:
                        self.speech_marks_dict[clean_word].append(variant)

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
        with open(self.pth.speech_marks_path, "w", encoding="utf-8") as f:
            json.dump(self.speech_marks_dict, f, ensure_ascii=False, indent=2)

    def _should_regenerate(self) -> bool:
        """Check if cache is older than 1 day"""
        return (
            not self.pth.speech_marks_path.exists()
            or datetime.now()
            - datetime.fromtimestamp(self.pth.speech_marks_path.stat().st_mtime)
            > timedelta(days=1)
        )

    def regenerate_from_db(self):
        """Regenerate speech marks from database (migrated from SandhiContractionManager)."""
        db_session: Session = get_db_session(self.pth.dpd_db_path)

        # only include words with meaning_1
        db = db_session.query(DpdHeadword).filter(DpdHeadword.meaning_1 != "").all()

        for i in db:
            fields_to_check = [i.example_1, i.example_2, i.commentary]
            for field in fields_to_check:
                if field and "'" in field:
                    for word in self._replace_split(field):
                        if "'" in word:
                            word_clean = word.replace("'", "")
                            if word not in self._exceptions:
                                self.update_variants(word_clean, word)

        db_session.close()
        self.save()

    def _replace_split(self, string: str) -> list[str]:
        """Clean and split a string into words (migrated from SandhiContractionManager)."""
        replacements = [
            ("<b>", ""),
            ("</b>", ""),
            ("<i>", ""),
            ("</i>", ""),
            (".", " "),
            (",", " "),
            (";", " "),
            ("!", " "),
            ("?", " "),
            ("/", " "),
            ("-", " "),
            ("{", " "),
            ("}", " "),
            ("(", " "),
            (")", " "),
            ("[", " "),
            ("]", " "),
            (":", " "),
            ("\n", " "),
            ("\r", " "),
            ("…", " "),
        ]
        for old, new in replacements:
            string = string.replace(old, new)
        return string.split(" ")
