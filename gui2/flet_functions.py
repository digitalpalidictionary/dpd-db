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


def process_bold_tags(text: str):
    """Convert text with bold tags to styled TextSpans"""
    spans = []
    parts = text.split("<b>")

    # First part before any <b> tag
    if parts[0]:
        spans.append(ft.TextSpan(parts[0]))

    for part in parts[1:]:
        if "</b>" in part:
            bold_text, rest = part.split("</b>", 1)
            spans.append(
                ft.TextSpan(
                    bold_text,
                    style=ft.TextStyle(
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_200,
                    ),
                )
            )
            if rest:
                spans.append(ft.TextSpan(rest))
        else:
            # Unclosed <b> tag - make whole remaining text bold
            spans.append(
                ft.TextSpan(part, style=ft.TextStyle(weight=ft.FontWeight.BOLD))
            )

    return spans
