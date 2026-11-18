"""Size and read time of one word's recordings. Run: uv run kamma/threads/20261118_preview_inflection_table/artifacts/audio_probe.py"""

import time

from audio.db.db_helpers import get_audio_record

for word in ("a", "dhamma", "akakkasa"):
    for gender in ("male1", "male2", "female1"):
        t = time.perf_counter()
        data = get_audio_record(word, gender)
        ms = (time.perf_counter() - t) * 1000
        print(word, gender, len(data) if data else None, f"{ms:.0f} ms")
