import time
import os
import psutil
from sqlalchemy.orm import defer
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def get_mem():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


pth = ProjectPaths()
session = get_db_session(pth.dpd_db_path)

print(f"Initial Memory: {get_mem():.2f} MB")
start = time.time()
# Defer large columns
db = (
    session.query(DpdHeadword)
    .options(
        defer(DpdHeadword.inflections_html),
        defer(DpdHeadword.freq_html),
        defer(DpdHeadword.inflections_sinhala),
        defer(DpdHeadword.inflections_devanagari),
        defer(DpdHeadword.inflections_thai),
        defer(DpdHeadword.freq_data),
    )
    .all()
)
duration = time.time() - start
print(f"Loaded {len(db)} headwords (deferred large columns) in {duration:.2f}s")
print(f"Memory After Load: {get_mem():.2f} MB")

session.close()
