import sys

from db.audio.bhashini import Bashini
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.title("bashini tts")

    pr.green("loading db")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    seen_headwords: set[str] = set()
    pr.yes(len(db))

    pr.green("init bashini tts")
    bashini = Bashini(
        language="Kannada",
        voice_name="kn-f4",
        voice_style="Neutral",
        speech_rate=0.85,
    )
    pr.yes("ok")

    try:
        for db_count, i in enumerate(db):
            remaining = len(db) - db_count
            if i.lemma_clean not in seen_headwords:
                bashini.tts(i.lemma_clean, remaining)
                seen_headwords.add(i.lemma_clean)
    except KeyboardInterrupt:
        pr.green(f"\n{len(db) - db_count} words remaining to process")
        sys.exit(0)


if __name__ == "__main__":
    main()


# need a solution for problem files
# just re-making them doesn't solve the problem, just repeats it.
# 1. make a folder for wrong files
# 2. use another voice to create them?
#
