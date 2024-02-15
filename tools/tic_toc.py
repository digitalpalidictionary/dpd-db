"""Simple timer for modules or parts of code."""

import time
from datetime import datetime
from rich import print

line = "-"*40


def tic():
    """Start the clock"""
    global ticx
    ticx = datetime.now()


def toc():
    "Stop the clock and print a line and elapsed time."
    tocx = datetime.now()
    tictoc = (tocx - ticx)
    print(f"[cyan]{line}")
    print(f"[cyan]{tictoc}")
    print()


def bip():
    """Start a mini clock."""
    global start_time
    start_time = time.time()


def bop():
    "End the mini clock and return elapsed time."
    elapsed_time = time.time() - start_time
    return f"{elapsed_time:.3f}"
    # return round(elapsed_time, 3)


def pbop():
    "End the mini clock and print elapsed time."
    elapsed_time = time.time() - start_time
    print(f"{elapsed_time:.3f}")
    # return round(elapsed_time, 3)


def today():
    now = datetime.now()
    today = now.strftime("%d")
    return today

# timeis()
