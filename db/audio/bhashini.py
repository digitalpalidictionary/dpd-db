import json
import time
from pathlib import Path

import requests
from aksharamukha import transliterate
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class Bashini:
    api_url = "https://tts.bhashini.ai//v1/synthesize"
    api_key = config_read("apis", "bhashini")
    output_dir = Path("db/audio/bhashini")
    if not output_dir.exists():
        output_dir.mkdir()
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": f"{api_key}",
    }
    subdir_name: Path
    output_path: Path
    completed_count: int = 0

    def transliterate_text(self, language: str, text_roman: str):
        if language in ["Sanskrit", "Marathi"]:
            language = "Devanagari"
        return transliterate.process(
            "IASTPali",
            language,
            text_roman,
            nativize=False,
        )

    def tts(
        self,
        text_roman: str,
        language: str,
        voice_name: str,
        voice_style: str,
    ):
        text_transliterated = self.transliterate_text(language, text_roman)

        payload = {
            "text": f"{text_transliterated}.",
            "language": language,
            "voiceName": voice_name,
            "voiceStyle": voice_style,
        }
        self.filename = Path(text_roman).with_suffix(".mp3")
        self.subdir_name = self.output_dir.joinpath(
            f"{language}_{voice_name}_{voice_style}"
        )
        if not self.subdir_name.exists():
            self.subdir_name.mkdir()
        self.output_path = self.subdir_name / self.filename

        #  TODO rather make a new numbered copy
        if self.output_path.is_file():
            return

        self.completed_count += 1
        pr.info(f"[{self.completed_count}] synthesizing: {self.output_path}")

        # Simple retry logic - 3 attempts
        for attempt in range(3):
            try:
                resp = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=30,  # 30-second
                )
                break  # Success, exit retry loop
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:
                if attempt == 2:  # Last attempt failed
                    pr.error(f"Connection failed after 3 attempts: {str(e)}")
                    return
                pr.warning(f"Connection error, retrying ({attempt + 1}/3)...")
                time.sleep(1)  # Simple 1-second delay between retries
        try:
            resp.raise_for_status()
        except Exception as e:
            pr.red(str(e))

        if resp.headers.get("Content-Type", "").startswith("audio"):
            audio_bytes = resp.content
            with open(self.output_path, "wb") as f:
                f.write(audio_bytes)
        else:
            pr.red(resp.text)


def iterate_through_dpd():
    bashini = Bashini()
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    seen_headwords: set[str] = set()

    language = "Kannada"
    voice = "kn-m4"
    style = "Neutral"

    for i in db:
        if i.lemma_clean not in seen_headwords:
            bashini.tts(i.lemma_clean, language, voice, style)
            seen_headwords.add(i.lemma_clean)


if __name__ == "__main__":
    iterate_through_dpd()

# need a solution for problem files, just re-making them
# doesn't solve the problem, just repeats it.
# 1. make a folder for wrong files
# 2. use another voice to create them
#
