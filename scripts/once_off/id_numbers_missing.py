from db.get_db_session import get_db_session
from db.models import PaliWord


def main():
    db_session = get_db_session("dpd.db")
    db = db_session.query(PaliWord)
    db = sorted(db, key=lambda x: x.id)

    for count, i in enumerate(db):
        print(f"count: {count+1:<10}id: {i.id}")
        if count+1 != i.id:
            break


if __name__ == "__main__":
    main()
