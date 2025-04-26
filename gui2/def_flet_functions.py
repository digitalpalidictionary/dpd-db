import flet as ft
import re


def highlight_word_in_sentence(word, sentence, color=ft.Colors.BLUE_200):
    """Turns paragraph of text into a list of TextSpan."""

    sentence = re.sub("'", "", sentence)

    spans = []
    parts = re.split(word, sentence)

    for i, part in enumerate(parts):
        spans.append(ft.TextSpan(part))
        if i != len(parts) - 1:
            spans.append(
                ft.TextSpan(
                    word,
                    style=ft.TextStyle(color=color),
                )
            )

    return spans
