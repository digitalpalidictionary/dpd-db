import os
import time

import psutil

from db.db_helpers import get_db_session
from exporter.webapp.preloads import (
    make_ascii_to_unicode_dict,
    make_headwords_clean_set,
    make_roots_count_dict,
)
from tools.cache_load import load_audio_dict
from tools.paths import ProjectPaths

pth = ProjectPaths()
session = get_db_session(pth.dpd_db_path)


def get_mem():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def measure(func, name):
    mem_before = get_mem()
    start = time.time()
    res = func(session)
    duration = time.time() - start
    mem_after = get_mem()
    print(
        f"{name}: {duration:.2f}s, Memory Delta: {mem_after - mem_before:.2f} MB, Total: {mem_after:.2f} MB"
    )
    return res


print(f"Initial Memory: {get_mem():.2f} MB")
roots_count_dict = measure(make_roots_count_dict, "make_roots_count_dict")
headwords_clean_set = measure(make_headwords_clean_set, "make_headwords_clean_set")
ascii_to_unicode_dict = measure(
    make_ascii_to_unicode_dict, "make_ascii_to_unicode_dict"
)

measure(lambda s: load_audio_dict(), "load_audio_dict")
