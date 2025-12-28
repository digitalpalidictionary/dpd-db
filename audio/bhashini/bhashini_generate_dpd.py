import sys

from audio.bhashini.bhashini_class import Bashini
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def test_word_length(word: str, length: int) -> bool:
    """Only True for words less than a certain length"""

    only_short_words = False
    if only_short_words is False:
        return True
    elif only_short_words and len(word) < length:
        return True
    else:
        return False


def main():
    pr.title("bashini tts")

    for voice_name in ["kn-m4", "kn-m1", "kn-f4"]:
        pr.green_title(voice_name)

        bashini = Bashini(
            language="Kannada",
            voice_name=voice_name,
            voice_style="Neutral",
            speech_rate=0.85,
            play_audio=True,
            overwrite=False,
            problem=False,
        )

        if bashini.ping_api():
            pr.green("loading data")
            pth = ProjectPaths()
            db_session = get_db_session(pth.dpd_db_path)
            db = db_session.query(DpdHeadword).all()

            pr.yes(len(db))

            seen_headwords: set[str] = set()
            try:
                for db_count, i in enumerate(db):
                    remaining = len(db) - db_count
                    if i.lemma_clean not in seen_headwords:
                        if test_word_length(i.lemma_clean, 5):
                            bashini.tts_dpd(i.lemma_clean, remaining)
                            seen_headwords.add(i.lemma_clean)

            except KeyboardInterrupt:
                pr.green(f"\n{len(db) - db_count} words remaining to process\n")
                sys.exit(0)


if __name__ == "__main__":
    main()


# need a solution for problem files
# just re-making them doesn't solve the problem, just repeats it.
# 1. make a folder for wrong files
# 2. use another voice to create them?

# Favourites

# male 1
# language="Kannada",
# voice_name="kn-m4",
# voice_style="Neutral",
# speech_rate=0.85,

# female
# language="Kannada",
# voice_name="kn-f4",
# voice_style="Neutral",
# speech_rate=0.85,
