import time
from exporter.webapp.preloads import make_roots_count_dict, make_headwords_clean_set, make_ascii_to_unicode_dict
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

pth = ProjectPaths()
session = get_db_session(pth.dpd_db_path)

def measure(func, name):
    start = time.time()
    res = func(session)
    print(f"{name}: {time.time()-start:.4f}s")
    return res

print("Measuring preloads...")
measure(make_roots_count_dict, "make_roots_count_dict")
measure(make_headwords_clean_set, "make_headwords_clean_set")
measure(make_ascii_to_unicode_dict, "make_ascii_to_unicode_dict")
