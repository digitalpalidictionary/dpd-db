from datetime import datetime
from timeit import default_timer as timer
from datetime import timedelta


blue = "\033[38;5;33m"  # blue
green = "\033[38;5;34m"  # green
red = "\033[38;5;160m"  # red
yellow = "\033[38;5;220m"  # yellow
white = "\033[38;5;251m"  # white
orange = "\033[38;5;172m"  # orange
cyan = "\033[38;5;14m"  # cyan
line = "-"*40


def timeis():
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return (f"{blue}{current_time}{white}")


def timeiz(details):
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{blue}{current_time}{white} {details}")


def tic():
    global ticx
    ticx = datetime.now()


def toc():
    tocx = datetime.now()
    tictoc = (tocx - ticx)
    # print(f"{timeis()} {line}")
    # print(f"{timeis()} {cyan}{tictoc}")
    # print(f"{timeis()} {line}")
    # print(f"{timeis()}")

    print(f"{cyan}{line}")
    print(f"{cyan}{tictoc}")
    print()


def bip():
    global bipx
    bipx = timer()


def bop():
    bopx = timer()
    bipbop = timedelta(seconds=bopx-bipx)
    return bipbop


def today():
    now = datetime.now()
    today = now.strftime("%d")
    return today

# timeis()
