import time
import os
import psutil
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
db = session.query(DpdHeadword).all()
duration = time.time() - start
print(f"Loaded {len(db)} headwords in {duration:.2f}s")
print(f"Memory After Load: {get_mem():.2f} MB")

# Access some fields to force loading if lazy (though these are columns)
for i in db[:100]:
    _ = i.inflections_html
    _ = i.freq_html

print(f"Memory After Accessing HTML fields: {get_mem():.2f} MB")
