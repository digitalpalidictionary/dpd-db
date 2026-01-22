import time
import os
import psutil
from aksharamukha import transliterate

def get_mem():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

print(f"Initial Memory: {get_mem():.2f} MB")
start = time.time()
transliterate.process("IASTPali", "IPA", "test")
print(f"Memory after first aksharamukha: {get_mem():.2f} MB, Time: {time.time()-start:.4f}s")

for i in range(100):
    transliterate.process("IASTPali", "IPA", f"test_{i}")
print(f"Memory after 100 aksharamukha: {get_mem():.2f} MB")
