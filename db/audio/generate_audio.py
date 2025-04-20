#!/usr/bin/env python3

"""Find the most frequent words and generate audio files using ElevenLabs."""

from dataclasses import dataclass, field
from pathlib import Path
import traceback

from aksharamukha import transliterate
from elevenlabs import VoiceSettings
from rich import print
from sqlalchemy import desc
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from elevenlabs.client import ElevenLabs


@dataclass
class VoxItem:
    lemma_clean: str = ""
    lemma_1s: list[str] = field(default_factory=list)
    ebt_count: int = 0
    devanagari: str = ""
    file_name: Path = Path()


class VoxManager:
    def __init__(self):
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.db: list[DpdHeadword] = (
            self.db_session.query(DpdHeadword)
            .order_by(desc(DpdHeadword.ebt_count))
            .limit(10000)
            .all()
        )

        self.output_dir: Path = Path("db/audio/mp3")
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
                vox.file_name = self.output_dir / f"{i.lemma_clean}.mp3"
            else:
                self.vox_unprocessed[i.lemma_clean].lemma_1s.append(i.lemma_1)

    def convert_to_devanagari(self, text: str) -> str:
        text_trans = transliterate.process(
            "IASTPali",
            "Devanagari",
            text,
            nativize=True,
            post_options=["devanagariuttara", "ShowSchwaHindi"],
        )
        if text_trans:
            return text_trans
        else:
            return text


class ElevenLabsManager:
    api_key = config_read("apis", "eleven_labs")
    client = ElevenLabs(
        api_key=api_key,
    )

    voices = {
        "kanika": "XcWoPxj7pwnIgM3dQnWv",
        "brian": "nPczCjzI2devNBz1zQrb",
    }
    voice = "kanika"
    voice_id = voices[voice]
    output_format = "mp3_44100_128"
    text: str
    model_id: str = "eleven_multilingual_v2"
    overwrite: bool = False

    def generate_and_save_audio(self, vox_item: VoxItem) -> None:
        """Generates audio for the given text and saves it to output_path."""

        pr.green(vox_item.lemma_clean)

        if vox_item.file_name.exists() and self.overwrite is False:
            pr.no("skipping")

        else:
            try:
                response = self.client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    output_format=self.output_format,
                    text=f"{vox_item.devanagari}.",
                    model_id=self.model_id,
                    voice_settings=VoiceSettings(speed=0.8, stability=0.7),
                )

                output_file = vox_item.file_name.with_stem(
                    f"{vox_item.lemma_clean}_{self.voice}"
                )

                with open(output_file, "wb") as f:
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

    for vox_item in vox_manager.vox_unprocessed.values():
        eleven_labs_manager.generate_and_save_audio(vox_item)

    pr.toc()


if __name__ == "__main__":
    main()
