from audio.bhashini.bhashini_class import Bashini


text = "dhaṃ"


bashini = Bashini(
    language="Kannada",
    voice_name="kn-m4",
    voice_style="Neutral",
    speech_rate=0.85,
    play_audio=True,
    overwrite=False,
    problem=True,
)

bashini.tts_single(text)
