from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.clean_machine import clean_machine


def main():
    db_session = get_db_session("dpd.db")
    db = db_session.query(PaliWord)
    english_vocab: set = set()

    for i in db:
        clean_meaning = clean_machine(i.meaning_1)
        english_vocab.update(clean_meaning.split(" "))

    for counter, i in enumerate(sorted(english_vocab)):
        print(f"{counter:<10}{i}")
    print(len(english_vocab))


if __name__ == "__main__":
    main()
