from sqlalchemy import func
from db.db_helpers import get_db_session
from db.models import DbInfo
from tools.paths import ProjectPaths

pth = ProjectPaths()
session = get_db_session(pth.dpd_db_path)

res = session.query(DbInfo.key, func.length(DbInfo.value)).all()
for k, v in res:
    print(f"{k}: {v/1024:.2f} KB")

session.close()
