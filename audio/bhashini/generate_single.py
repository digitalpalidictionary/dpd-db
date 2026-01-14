from audio.bhashini.bhashini_class import Bashini


text = "mayañhi"


bashini = Bashini(
    language="Kannada",
    voice_name="kn-m4",
    voice_style="Neutral",
    speech_rate=0.85,
    play_audio=True,
    overwrite=True,
    problem=False,
)

bashini.tts_single(text)
