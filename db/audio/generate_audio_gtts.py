#!/usr/bin/env python3

"""Find the most frequent words and generate audio files using gTTS."""

import time
import subprocess
from pathlib import Path

from aksharamukha import transliterate
from gtts import gTTS
from rich import print
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class TtsManager:
    def __init__(self):
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()

        self.all_words_dict: dict[str, str] = {}

        for i in self.db:
            self.all_words_dict[i.lemma_clean] = ""

        self.output_dir: Path = Path("db/audio/mp3")

    def convert_to_devanagari(self, text: str) -> str:
        text_trans = transliterate.process(
            "IASTPali",
            "Devanagari",
            text,
            post_options=["ShowSchwaHindi"],
        )
        if text_trans:
            return text_trans
        else:
            return text

    def convert_to_kannada(self, text: str) -> str:
        text_trans = transliterate.process(
            "IASTPali",
            "Kannada",
            text,
        )
        if text_trans:
            return text_trans
        else:
            return text

    def process(self, word: str) -> None:
        """Make hindi, kannada"""

        pr.green_title(word)

        # hindi
        self.lang = "hi"
        self.text = f"{self.convert_to_devanagari(word)}."
        pr.white(self.text)
        self.file_path = self.output_dir / f"{word}_hi.mp3"
        self.tts_convert_and_save()
        pr.yes("")

        # kannada
        self.lang = "kn"
        self.text = f"{self.convert_to_kannada(word)}."
        pr.white(self.text)
        self.file_path = self.output_dir / f"{word}_kn.mp3"
        self.tts_convert_and_save()
        pr.yes("")

    def tts_convert_and_save(self) -> None:
        tts = gTTS(text=self.text, lang_check=True, lang=self.lang)
        tts.save(self.file_path)
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", str(self.file_path)],
            check=True,
            capture_output=True,
        )
        time.sleep(2)


def main():
    pr.tic()
    pr.title("generating tts files")
    tts = TtsManager()

    for word in tts.all_words_dict:
        tts.process(word)

    pr.toc()


if __name__ == "__main__":
    main()
