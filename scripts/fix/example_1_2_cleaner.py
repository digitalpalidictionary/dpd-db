#!/usr/bin/env python3

"""Bulk-clean example_1 / example_2 for headwords that still lack meaning_1.

Applies speech-mark expansion, text normalization, and bracket removal via the
same tools.example_cleaning helpers that gui2 exposes as per-word buttons — but
sweeps every incomplete word in one pass instead of one at a time.
"""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.example_cleaning import clean_example, remove_brackets
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    speech_marks_manager = SpeechMarkManager()

    for counter, i in enumerate(db):
        if i.meaning_1 == "":
            if i.example_1:
                i.example_1 = remove_brackets(
                    clean_example(i.example_1, speech_marks_manager)
                )
                pr.green("")
                pr.green(i.lemma_1)
                pr.green(i.example_1)

            if i.example_2:
                i.example_2 = remove_brackets(
                    clean_example(i.example_2, speech_marks_manager)
                )
                pr.green("")
                pr.green(i.lemma_1)
                pr.green(i.example_2)

    db_session.commit()


if __name__ == "__main__":
    main()
