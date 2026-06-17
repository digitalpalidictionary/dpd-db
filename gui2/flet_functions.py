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


def highlight_terms(text: str, terms: list[tuple[str, str]]) -> list[ft.TextSpan]:
    """Return TextSpans for ``text`` with each non-empty ``(term, colour)``
    highlighted wherever it occurs (case-insensitive, literal substring match).

    Unlike colouring the whole control, this tints only the matched word/phrase
    in place, leaving the rest of the text its normal colour.
    """
    active = [(term, colour) for term, colour in terms if term]
    if not active:
        return [ft.TextSpan(text)]
    pattern = re.compile(
        "(" + "|".join(re.escape(term) for term, _ in active) + ")",
        re.IGNORECASE,
    )
    colour_of = {term.lower(): colour for term, colour in active}
    spans: list[ft.TextSpan] = []
    for piece in pattern.split(text):
        if not piece:
            continue
        colour = colour_of.get(piece.lower())
        style = ft.TextStyle(color=colour) if colour else None
        spans.append(ft.TextSpan(piece, style=style))
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
