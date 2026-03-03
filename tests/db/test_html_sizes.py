from sqlalchemy import func
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

pth = ProjectPaths()
session = get_db_session(pth.dpd_db_path)

res = session.query(
    func.avg(func.length(DpdHeadword.inflections_html)),
    func.avg(func.length(DpdHeadword.freq_html)),
    func.max(func.length(DpdHeadword.inflections_html)),
    func.max(func.length(DpdHeadword.freq_html)),
    func.sum(func.length(DpdHeadword.inflections_html)),
    func.sum(func.length(DpdHeadword.freq_html)),
).first()

print(f"Avg Inflections HTML: {res[0]:.2f} bytes")
print(f"Avg Freq HTML: {res[1]:.2f} bytes")
print(f"Max Inflections HTML: {res[2]} bytes")
print(f"Max Freq HTML: {res[3]} bytes")
print(f"Total Inflections HTML: {res[4] / 1024 / 1024:.2f} MB")
print(f"Total Freq HTML: {res[5] / 1024 / 1024:.2f} MB")

session.close()
