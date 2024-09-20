"""Find and remove fields with None / NULL in the DpdHeadword table."""

from sqlalchemy import inspect
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

inspector = inspect(DpdHeadword)
column_names = [column.name for column in inspector.columns]

db = db_session.query(DpdHeadword)

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
