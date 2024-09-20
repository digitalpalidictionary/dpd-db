from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.clean_machine import clean_machine
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword)
    english_vocab: set = set()

    for i in db:
        if i.meaning_1 is None:
            continue
        clean_meaning = clean_machine(i.meaning_1)
        english_vocab.update(clean_meaning.split(" "))

    for counter, i in enumerate(sorted(english_vocab)):
        print(f"{counter:<10}{i}")
    print(len(english_vocab))


if __name__ == "__main__":
    main()
