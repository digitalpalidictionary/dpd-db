import time

from db.db_helpers import get_db_session
from exporter.webapp.preloads import (
    make_ascii_to_unicode_dict,
    make_headwords_clean_set,
    make_roots_count_dict,
)
from tools.paths import ProjectPaths


def measure(func, name, session):
    start = time.time()
    res = func(session)
    print(f"{name}: {time.time() - start:.4f}s")
    return res


def main():
    pth = ProjectPaths()
    session = get_db_session(pth.dpd_db_path)
    print("Measuring preloads...")
    measure(make_roots_count_dict, "make_roots_count_dict", session)
    measure(make_headwords_clean_set, "make_headwords_clean_set", session)
    measure(make_ascii_to_unicode_dict, "make_ascii_to_unicode_dict", session)


if __name__ == "__main__":
    main()
