from rich import print

from db.get_db_session import get_db_session
from db.models import PaliRoot

db_session = get_db_session("dpd.db")
roots_db = db_session.query(PaliRoot).all()

for i in roots_db:
    if i.root == "√pā":
        i.root = "√pā 2"

db_session.commit()
db_session.close()
