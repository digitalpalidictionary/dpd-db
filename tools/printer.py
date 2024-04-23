from rich import print
from tools.tic_toc import bop

def p_title(title: str) -> None:
    print(f"[bright_yellow]{title}")

def p_green(message: str) -> None:
    print(f"[green]{message:<35}")

def p_white(message):
    print(f"{'':<5}[white]{message:<30}", end="")

def p_yes(message):
    print(f"[blue]{message:<10}", end="")
    p_bop()

def p_no(message):
    print(f"[red]{message:<10}", end="")
    p_bop()

def p_red(message):
    print(f"[red]{message}")

def p_bop():
    print(f"{bop():>10}")