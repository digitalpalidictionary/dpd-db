import time
import os
import psutil
from tools.cache_load import load_cf_set, load_idioms_set, load_sutta_info_set

def get_mem():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def measure(func, name):
    mem_before = get_mem()
    start = time.time()
    res = func()
    duration = time.time() - start
    mem_after = get_mem()
    print(f"{name}: {duration:.2f}s, Memory Delta: {mem_after - mem_before:.2f} MB, Total: {mem_after:.2f} MB, Items: {len(res)}")
    return res

print(f"Initial Memory: {get_mem():.2f} MB")
measure(load_cf_set, "load_cf_set")
measure(load_idioms_set, "load_idioms_set")
measure(load_sutta_info_set, "load_sutta_info_set")
