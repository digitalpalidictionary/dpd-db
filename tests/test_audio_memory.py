import time
import os
import psutil
from tools.cache_load import load_audio_dict


def print_memory(label):
    process = psutil.Process(os.getpid())
    print(f"{label}: {process.memory_info().rss / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    print_memory("Start")
    start = time.time()
    d = load_audio_dict()
    print(f"Loaded {len(d)} items in {time.time() - start:.2f}s")
    print_memory("After load")
