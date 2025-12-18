"""Superscript numerals using Unicode or HTML."""

import re


def superscripter_html(text):
    """Superscipt text using html <sup>."""

    text = re.sub("( \\d.*$)", "<sup style='font-size: 75%;'>\\1</sup>", text)
    return text


def superscripter_uni(text):
    """Superscipt using unicode characters."""
    text = re.sub("( )(\\d)", "\u200a\\2", text)
    text = re.sub("0", "⁰", text)
    text = re.sub("1", "¹", text)
    text = re.sub("2", "²", text)
    text = re.sub("3", "³", text)
    text = re.sub("4", "⁴", text)
    text = re.sub("5", "⁵", text)
    text = re.sub("6", "⁶", text)
    text = re.sub("7", "⁷", text)
    text = re.sub("8", "⁸", text)
    text = re.sub("9", "⁹", text)
    text = re.sub("\\.", "·", text)
    return text
