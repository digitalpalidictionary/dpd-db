from rich import print
from tools.tic_toc import bip, bop

def p_title(title: str) -> None:
    print(f"[bright_yellow]{title}")
    bip()

def p_green_title(message: str) -> None:
    print(f"[green]{message}")
    bip()

def p_green(message: str) -> None:
    print(f"[green]{message:<35}", end="")
    bip()

def p_white(message):
    print(f"{'':<5}[white]{message:<30}", end="")
    bip()

def p_yes(message: int|str):
    if isinstance(message, int):
        print(f"[blue]{message:>10,}", end="")
    else:
        print(f"[blue]{message:>10}", end="")
    p_bop()

def p_no(message):
    print(f"[red]{message:>10}", end="")
    p_bop()

def p_red(message):
    print(f"[red]{message}")

def p_bop():
    print(f"{bop():>10}")

def p_counter(counter: int, total:int, word):
    print(f"{counter:>10,} / {total:<10,} {word[:20]:<20} {bop():>10}")
    bip()

def p_summary(key, value):
    print(f"[green]{key:<20}[/green]{value}")