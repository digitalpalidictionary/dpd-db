"""Find and remove fields with None / NULL in the PaliWord table."""

from sqlalchemy import inspect
from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths

PTH = ProjectPaths()
db_session = get_db_session(PTH.dpd_db_path)

inspector = inspect(PaliWord)
column_names = [column.name for column in inspector.columns]

db = db_session.query(PaliWord)

for row in db:
    columns = row.__dict__
    for column, data in columns.items():
        if data is None:
            if column != "updated_at":
                # if column == "family_word":
                print(f"{row.id} {column:<40}{data}")
#                 row.family_word = ""

# db_session.commit()
# db_session.close()
