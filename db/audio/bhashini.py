import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import requests
from aksharamukha import transliterate
from rich import print

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
    output_dir = Path("db/audio/bhashini")
    if not output_dir.exists():
        output_dir.mkdir()

    output_filepath: Path

    def __init__(
        self,
        language: str,
        voice_name: str,
        voice_style: str,
        speech_rate: float,
        debug: bool = False,
        play_audio: bool = False,
    ):
        self.language = language
        self.voice_name = voice_name
        self.voice_style = voice_style
        self.speech_rate = speech_rate

        self.completed: int = 0

        self.debug = debug
        self.play_audio = play_audio

        # Create output subdir based on language settings
        self.output_subdir = self.output_dir.joinpath(
            f"{self.language}_{self.voice_name}_{self.voice_style}"
        )
        if not self.output_subdir.exists():
            self.output_subdir.mkdir()

    def tts(self, text_roman: str, remaining: int):
        """
        Bashini Text to Speech

        :param text_roman: The text to synthesize in Roman unicode.
        :type text_roman: str
        :param remaining: A counter to display
        :type remaining: int
        """

        # individual filepath
        self.file_name = Path(text_roman).with_suffix(".mp3")
        self.output_filepath = self.output_subdir / self.file_name

        #  TODO rather make a new numbered copy?
        if self.output_filepath.is_file():
            return

        text_transliterated = self._transliterate_text(text_roman)
        text_for_api = f"। {text_transliterated} ।"

        payload = {
            "text": text_for_api,
            "language": self.language,  # "Sanskrit"
            "voiceName": self.voice_name,
            "voiceStyle": self.voice_style,
            "speechRate": self.speech_rate,
        }

        pr.info(f"{self.completed} / {remaining} {self.output_filepath} {text_for_api}")

        # Simple retry logic - 3 attempts
        for attempt in range(3):
            try:
                resp = requests.post(
                    self.tts_api_url,
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
            self._handle_audio(audio_bytes)
        else:
            pr.red(resp.text)

    def _transliterate_text(self, text_roman: str):
        return transliterate.process(
            "IASTPali",
            self.language,
            # "Devanagari",
            text_roman,
            nativize=True,
            post_options=["PreserveSource", "useDandas"],  # Kannada
            # post_options=["DevanagariAnusvara"],  # Devanagari
        )

    def _handle_audio(self, audio_bytes: bytes) -> None:
        """Handle audio playback and saving based on debug settings."""
        should_save = True

        if self.debug:
            should_save = self._debug_playback(audio_bytes)

        if should_save:
            self._save_audio(audio_bytes)

        if self.play_audio and not self.debug:
            self._play_audio(self.output_filepath)

    def _debug_playback(self, audio_bytes: bytes) -> bool:
        """Debug mode: play audio and ask user whether to save."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name

        try:
            while True:
                self._play_audio(temp_file_path)
                user_input = input(
                    "Press 's' to save, 'r' to replay, any other key to pass: "
                )
                print(user_input)  # Echo the character for feedback

                if user_input.lower() == "r":
                    continue
                elif user_input.lower() == "s":
                    return True
                else:
                    pr.warning("Skipped saving.")
                    return False
        except subprocess.CalledProcessError as e:
            pr.error(f"Error playing audio: {e}")
            return False
        except FileNotFoundError:
            pr.error("ffplay not found. Please install ffmpeg.")
            return False
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _save_audio(self, audio_bytes: bytes) -> None:
        """Save audio bytes to file."""
        with open(self.output_filepath, "wb") as f:
            f.write(audio_bytes)
            self.completed += 1
        if self.debug:
            pr.info(f"Saved: {self.output_filepath}")

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
                check=True,
            )
        except subprocess.CalledProcessError as e:
            pr.error(f"Error playing audio: {e}")
        except FileNotFoundError:
            pr.error("ffplay not found. Please install ffmpeg.")

    @staticmethod
    def ping_api() -> bool:
        """Test Bhashini API connectivity with a minimal request."""
        import time

        # Minimal test payload
        test_payload = {
            "text": "test",
            "language": "Kannada",
            "voiceName": "kn-f4",
            "voiceStyle": "Neutral",
            "speechRate": 1.0,
        }

        start_time = time.time()

        try:
            pr.green("pinging API")
            resp = requests.post(
                Bashini.tts_api_url,
                headers=Bashini.headers,
                data=json.dumps(test_payload),
                timeout=10,  # 10-second timeout for quick ping
            )
            resp.raise_for_status()
            result = resp.headers.get("Content-Type", "").startswith("audio")
            response_time = time.time() - start_time
            pr.yes(f"{response_time:.2f} sec")
            return result

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:
            pr.no("fail")
            pr.red(str(e))
            return False
        except Exception as e:
            pr.no("fail")
            pr.red(str(e))
            return False
