import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

import requests
from aksharamukha import transliterate

from tools.configger import config_read
from tools.printer import printer as pr


class Bashini:
    # Global options
    api_key = config_read("apis", "bhashini")
    tts_api_url = "https://tts.bhashini.ai/v1/synthesize"

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": f"{api_key}",
    }

    # dirs, subdirs and files
    output_dir = Path("audio/mp3s")

    def __init__(
        self,
        language: str,
        voice_name: str,
        voice_style: str,
        speech_rate: float,
        play_audio: bool = False,
        overwrite: bool = False,
        problem: bool = False,
    ):
        """
        Initialize the Bashini TTS class.

        :param language: The language code (e.g., 'Kannada').
        :param voice_name: The specific voice identifier (e.g., 'kn-m4').
        :param voice_style: The style of the voice (e.g., 'Neutral').
        :param speech_rate: Speed of speech (e.g., 0.85).
        :param play_audio: If True, plays the audio after generation. Defaults to False.
        :param overwrite: If True, overwrites existing audio files. Defaults to False.
        :param problem: If True, uses specific text formatting for problematic files. Defaults to False.
        """
        self.language = language
        self.voice_name = voice_name
        self.voice_style = voice_style
        self.speech_rate = speech_rate

        self.completed: int = 0

        self.play_audio = play_audio
        self.overwrite = overwrite
        self.problem = problem

        # Ensure output directory exists
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create output subdir based on language settings
        self.output_subdir = self.output_dir.joinpath(
            f"{self.language}_{self.voice_name}_{self.voice_style}_{str(self.speech_rate)}"
        )
        if not self.output_subdir.exists():
            self.output_subdir.mkdir(parents=True, exist_ok=True)

    def tts_dpd(self, text_roman: str, remaining: int):
        """
        Bashini Text to Speech

        :param text_roman: The text to synthesize in Roman unicode.
        :type text_roman: str
        :param remaining: A counter to display
        :type remaining: int
        """

        # individual filepath
        file_name = Path(text_roman).with_suffix(".mp3")
        output_filepath = self.output_subdir / file_name

        # don't overwrite existing files unless specifically instructed
        if output_filepath.is_file() and not self.overwrite:
            return

        text_for_api = self._prepare_text(text_roman)
        pr.info(f"{self.completed} | {remaining} {output_filepath} {text_for_api}")

        self._process_tts(text_for_api, output_filepath)

    def tts_single(self, text_roman: str):
        """
        Bashini Text to Speech for Single Usage

        :param text_roman: The text to synthesize in Roman unicode.
        :type text_roman: str
        """

        # Create output subdir for single files
        single_dir = self.output_dir / "single"
        if not single_dir.exists():
            single_dir.mkdir(parents=True, exist_ok=True)

        # generate filename: timestamp_voice_name_first20chars.mp3
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_text = (
            "".join(c for c in text_roman[:20] if c.isalnum() or c in (" ", "_", "-"))
            .strip()
            .replace(" ", "_")
        )
        file_name = Path(f"{timestamp}_{self.voice_name}_{safe_text}.mp3")
        output_filepath = single_dir / file_name

        text_for_api = self._prepare_text(text_roman)
        pr.info(f"Generating: {output_filepath}")

        self._process_tts(text_for_api, output_filepath)

    def _process_tts(self, text_for_api: str, output_filepath: Path):
        """Common logic to make request and handle audio."""
        audio_bytes = self._make_request(text_for_api)
        if audio_bytes:
            self._handle_audio(audio_bytes, output_filepath)

    def _prepare_text(self, text_roman: str) -> str:
        text_transliterated = self.translit_with_aksharamukha(text_roman)

        # often short words don't get pronounced by the ai, so repeat them twice
        if self.problem or len(text_roman) < 5:
            text_for_api = f"--- {text_transliterated} ... {text_transliterated} ... {text_transliterated} ... ---"
        else:
            text_for_api = f"। {text_transliterated} ।"
        return text_for_api

    def _make_request(self, text_for_api: str) -> bytes | None:
        payload = {
            "text": text_for_api,
            "language": self.language,
            "voiceName": self.voice_name,
            "voiceStyle": self.voice_style,
            "speechRate": self.speech_rate,
        }

        resp = self._post_to_api(payload)

        if not resp:
            return None

        try:
            resp.raise_for_status()
        except Exception as e:
            pr.red(str(e))
            return None

        if resp.headers.get("Content-Type", "").startswith("audio"):
            return resp.content
        else:
            pr.red(resp.text)
            return None

    @classmethod
    def _post_to_api(cls, payload: dict) -> requests.Response | None:
        """Send request to Bhashini API with retry logic."""
        for attempt in range(3):
            try:
                resp = requests.post(
                    cls.tts_api_url,
                    headers=cls.headers,
                    data=json.dumps(payload),
                    timeout=30,
                )
                return resp
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:
                if attempt == 2:  # Last attempt failed
                    pr.error(f"Connection failed after 3 attempts: {str(e)}")
                    return None
                pr.warning(f"Connection error, retrying ({attempt + 1}/3)...")
                time.sleep(1)
        return None

    def translit_with_aksharamukha(self, text_roman: str) -> str:
        result = transliterate.process(
            "IASTPali",
            self.language,
            # "Devanagari",
            text_roman,
            nativize=True,
            post_options=["PreserveSource", "useDandas"],  # Kannada
            # post_options=["DevanagariAnusvara"],  # Devanagari
        )
        return result or ""

    def _handle_audio(self, audio_bytes: bytes, output_filepath: Path) -> None:
        """Handle audio playback and saving based on play_audio settings."""
        self._save_audio(audio_bytes, output_filepath)

        if self.play_audio:
            self._play_audio(output_filepath)

    def _save_audio(self, audio_bytes: bytes, output_filepath: Path) -> None:
        """Save audio bytes to file."""
        with open(output_filepath, "wb") as f:
            f.write(audio_bytes)
            self.completed += 1

    def _play_audio(self, audio_path: Path | str) -> None:
        """Play audio file using ffplay."""
        try:
            subprocess.run(
                [
                    "ffplay",
                    "-nodisp",
                    "-autoexit",
                    "-loglevel",
                    "quiet",
                    str(audio_path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            pr.error(f"Error playing audio: {e}")
        except FileNotFoundError:
            pr.error("ffplay not found. Please install ffmpeg.")

    @classmethod
    def ping_api(cls) -> bool:
        """Test Bhashini API connectivity with a minimal request."""
        # Minimal test payload
        test_payload = {
            "text": "test",
            "language": "Kannada",
            "voiceName": "kn-f4",
            "voiceStyle": "Neutral",
            "speechRate": 1.0,
        }

        start_time = time.time()
        pr.green("pinging API")

        resp = cls._post_to_api(test_payload)

        if resp:
            try:
                resp.raise_for_status()
                result = resp.headers.get("Content-Type", "").startswith("audio")
                if result:
                    response_time = time.time() - start_time
                    pr.yes(f"{response_time:.2f} sec")
                    return True
                else:
                    pr.no("fail")
                    return False
            except Exception as e:
                pr.no("fail")
                pr.red(str(e))
                return False
        else:
            pr.no("fail")
            return False
