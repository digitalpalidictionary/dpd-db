"""Simple code timer for modules or parts of code."""

import time
from datetime import datetime


blue = "\033[38;5;33m"  # blue
green = "\033[38;5;34m"  # green
red = "\033[38;5;160m"  # red
yellow = "\033[38;5;220m"  # yellow
white = "\033[38;5;251m"  # white
orange = "\033[38;5;172m"  # orange
cyan = "\033[38;5;14m"  # cyan
line = "-"*40


def tic():
    global ticx
    ticx = datetime.now()


def toc():
    tocx = datetime.now()
    tictoc = (tocx - ticx)
    print(f"{cyan}{line}")
    print(f"{cyan}{tictoc}")
    print()


def bip():
    global start_time
    start_time = time.time()


def bop():
    elapsed_time = time.time() - start_time
    # return f"{elapsed_time:.2f}"
    return round(elapsed_time, 3)


def today():
    now = datetime.now()
    today = now.strftime("%d")
    return today

# timeis()
