from sqlalchemy import inspect
from db.get_db_session import get_db_session
from db.models import PaliWord

db_session = get_db_session("dpd.db")

inspector = inspect(PaliWord)
column_names = [column.name for column in inspector.columns]

db = db_session.query(PaliWord)

for row in db:
    columns = row.__dict__
    for column, data in columns.items():
        if data is None:
            if column != "updated_at":
                if column == "family_set":
                    print(f"{row.id} {column:<40}{data}")
                    row.family_set = ""

db_session.commit()
db_session.close()
