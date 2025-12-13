import json
from pathlib import Path

import requests
from aksharamukha import transliterate
from rich import print

from tools.configger import config_read
from tools.printer import printer as pr

test_text = """
etarahi.
kho.
pana.
bhante.
bhikkhuniyo.
bhagavato.
sāvikā.
viyattā.
vinītā.
visāradā.
bahussutā.
dhammadharā.
dhammānudhammappaṭipannā.
sāmīcippaṭipannā.
anudhammacāriniyo.
sakaṃ.
ācariyakaṃ.
uggahetvā.
ācikkhanti.
desenti.
paññapenti.
paṭṭhapenti.
vivaranti.
vibhajanti.
uttānīkaronti.
uppannaṃ.
parappavādaṃ.
sahadhammena.
suniggahitaṃ.
niggahetvā.
sappāṭihāriyaṃ.
dhammaṃ.
desenti..
parinibbātudāni.
bhante.
bhagavā.
parinibbātu.
sugato.
parinibbānakālodāni.
"""


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
    file_name: str
    output_path: Path

    def tts(
        self,
        text: str,
        language: str,
        voice_name: str,
        voice_style: str,
    ):
        payload = {
            "text": text,
            "language": language,
            "voiceName": voice_name,
            "voiceStyle": voice_style,
        }
        self.file_name = f"{language} {voice_name} {voice_style}"
        self.output_path = self.output_dir.joinpath(self.file_name).with_suffix(".mp3")

        if self.output_path.is_file():
            pr.warning(f"skipping: {self.output_path}")
            return

        pr.info(f"synthesizing: {self.output_path}")
        resp = requests.post(
            self.api_url,
            headers=self.headers,
            data=json.dumps(payload),
        )
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


def load_voices():
    voices_json_path = Path("db/audio/bhashini_voices.json")
    with open(voices_json_path) as f:
        return json.load(f)


def transliterate_text(language: str):
    if language in ["Sanskrit", "Marathi"]:
        language = "Devanagari"
    return transliterate.process(
        "IASTPali",
        language,
        test_text,
        nativize=False,
    )


def cycle_through_options():
    bashini = Bashini()
    voices_dict = load_voices()
    for _, voices in voices_dict.items():
        for voice in voices:
            id = voice.get("id")
            name = voice.get("name")
            language = voice.get("nativeLanguage")
            styles = voice.get("supportedStyles")

            text_trans = transliterate_text(language)

            for style in styles:
                text_trans = transliterate_text(language)
                if text_trans:
                    bashini.tts(text_trans, language, id, style)
                else:
                    pr.red(f"error transliterating to {language}")

                # add Sanskrit
                language2 = "Sanskrit"
                text_trans = transliterate_text(language2)
                if text_trans:
                    bashini.tts(text_trans, language2, id, style)
                else:
                    pr.red(f"error transliterating to {language2}")


if __name__ == "__main__":
    cycle_through_options()
