#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find the most frequent words and generate audio files using ElevenLabs."""

import time
import traceback
from dataclasses import dataclass, field
from json import dump
from pathlib import Path

from aksharamukha import transliterate
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr


@dataclass
class VoxItem:
    lemma_clean: str = ""
    lemma_1s: list[str] = field(default_factory=list)
    ebt_count: int = 0
    devanagari: str = ""
    kannada: str = ""


class VoxManager:
    def __init__(self):
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.db: list[DpdHeadword] = (
            self.db_session.query(DpdHeadword)
            # .order_by(desc(DpdHeadword.ebt_count))
            .limit(100)
            .all()
        )

        self.vox_unprocessed: dict[str, VoxItem] = {}
        self.make_vi_dict()

    def make_vi_dict(self):
        for count, i in enumerate(self.db):
            if i.lemma_clean not in self.vox_unprocessed:
                vox = VoxItem()
                self.vox_unprocessed[i.lemma_clean] = vox
                vox.lemma_clean = i.lemma_clean
                vox.lemma_1s = [i.lemma_1]
                vox.ebt_count = i.ebt_count
                vox.devanagari = self.convert_to_devanagari(i.lemma_clean)
                vox.kannada = self.convert_to_kannada(i.lemma_clean)
            else:
                self.vox_unprocessed[i.lemma_clean].lemma_1s.append(i.lemma_1)

    def convert_to_devanagari(self, text: str) -> str:
        text_trans = transliterate.process(
            "IASTPali",
            "Devanagari",
            text,
            nativize=False,
            post_options=["ShowSchwaHindi"],
        )
        if text_trans and text.endswith("a"):
            text_trans = text_trans + "a."

        if text_trans:
            return text_trans
        else:
            return text

    def convert_to_kannada(self, text: str) -> str:
        text_trans = transliterate.process(
            "IASTPali",
            "Kannada",
            text,
            nativize=False,
        )
        if text_trans:
            return text_trans
        else:
            return text


class ElevenLabsManager:
    def __init__(self):
        # --- API ---
        self.api_key = config_read("apis", "eleven_labs")
        self.client = ElevenLabs(api_key=self.api_key)

        # --- File ---
        self.output_dir: Path = Path("db/audio/mp3")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.voices = {
            "kanika": "XcWoPxj7pwnIgM3dQnWv",
            "brian": "nPczCjzI2devNBz1zQrb",
            "viraj": "1U02n4nD6AdIZ9CjF053",
            "kishan": "37frHvUllvzviJDpT2Qa",
            "amit": "Sxk6njaoa7XLsAFT7WcN",
            "netra": "nsuWityFzyjklsOeHYMt",
            "shanaya": "nsuWityFzyjklsOeHYMt",
            "zara": "ADd2WEtjmwokqUr0Y5Ad",
            "aaditya": "xMagNCpMgZ83QOEsHNre",
            "god": "PLFXYRTU74HpuNdj6oDl",
            "ruan": "IFINFMv1Samh9a9fDnWQ",
        }
        self.voice = "kanika"
        self.voice_id = self.voices[self.voice]
        self.output_format = "mp3_44100_128"
        self.model_id: str = "eleven_multilingual_v2"
        self.overwrite: bool = False
        self.language_code = "kan"

        # --- Voice Settings ---
        self.stability = 0.9
        self.similarity_boost = 0.5
        self.style = 0.1
        self.use_speaker_boost = False
        self.speed = 0.85
        self.seed = 12

    def save_settings(self):
        """Saves the configurable settings to a JSON file."""

        settings_to_save = {
            "voice": self.voice,
            "output_format": self.output_format,
            "model_id": self.model_id,
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost,
            "speed": self.speed,
        }
        with open(self.output_dir / "settings.json", "w") as f:
            dump(settings_to_save, f, indent=4)

    def generate_and_save_audio(self, vox_item: VoxItem) -> None:
        """Generates audio for the given text and saves it to output_path."""

        pr.green(vox_item.lemma_clean)

        file_path = self.output_dir / f"{vox_item.lemma_clean}.mp3"

        if file_path.exists() and self.overwrite is False:
            pr.no("skipping")

        else:
            try:
                response = self.client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    output_format=self.output_format,
                    text=f"{vox_item.devanagari}.",
                    model_id=self.model_id,
                    seed=self.seed,
                    voice_settings=VoiceSettings(
                        stability=self.stability,
                        similarity_boost=self.similarity_boost,
                        style=self.style,
                        use_speaker_boost=self.use_speaker_boost,
                        speed=self.speed,
                    ),
                )

                with open(file_path, "wb") as f:
                    for chunk in response:
                        if chunk:
                            f.write(chunk)

                pr.yes("saved")

            except Exception as e:
                pr.no("failed")
                pr.red(f"{e}")
                pr.red(traceback.format_exc())


def main():
    pr.tic()
    pr.title("generating audio files")
    vox_manager = VoxManager()
    eleven_labs_manager = ElevenLabsManager()

    eleven_labs_manager.save_settings()
    for vox_item in vox_manager.vox_unprocessed.values():
        eleven_labs_manager.generate_and_save_audio(vox_item)
        time.sleep(2)

    pr.toc()


if __name__ == "__main__":
    main()
