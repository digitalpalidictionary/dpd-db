"""Highligth bold and highlight a word in terminal output."""

import re
from rich import print


def terminal_bold(text: str, colour: str):
    """Turn bold tags into terminal colours.
    - 'text' is a string of text containing bold tags
    - 'colour' is your preferred colour in the terminal (rich print)
    """
    return text.replace("<b>", f"[{colour}]").replace("</b>", f"[/{colour}]")


def terminal_highlight(text: str, word: str, colour: str):
    """Turn bold tags into terminal colours.
    - 'text' is a string of text
    - 'word' is the word to be highlighted
    - 'colour' is your preferred colour in the terminal (rich print)
    """
    return re.sub(f"\\b{word}\\b", f"[{colour}]{word}[/{colour}]", text)


if __name__ == "__main__":
    print(terminal_bold("testing if <b>bold</b> highlights work", "cyan"))
    print(terminal_highlight("testing if bold highlights work", "bold", "cyan"))
