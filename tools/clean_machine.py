"""A text cleaning machine."""

import re
from rich import print


def clean_machine(text: str, niggahita="ṃ") -> str:
    """Return clean text with only allowable characters
    and optionally change the niggahita character."""

    allowed_characters = "aāiīuūeokgṅcjñṭḍṇtdnpbmyrlsvhḷṃṁ\n xfśṣǣæwqḥṛz"

    text = text.lower()
    text = re.sub(r"\d", "", text)
    text = re.sub(r"\t", "", text)
    text = re.sub(r"\n", r" \n", text)

    if niggahita == "ṃ":
        text = text.replace("ṁ", "ṃ")

    text = text.replace(".", " ")\
        .replace(",", " ")\
        .replace(";", " ")\
        .replace(":", " ")\
        .replace("'", "")\
        .replace("‘", "")\
        .replace("’", "")\
        .replace("`", "")\
        .replace("`", "")\
        .replace("“", "")\
        .replace("”", "")\
        .replace('"', "")\
        .replace("!", "")\
        .replace("?", "")\
        .replace("+", "")\
        .replace("*", "")\
        .replace("=", "")\
        .replace("~", "")\
        .replace("﻿", "")\
        .replace("§", " ")\
        .replace("‡", " ")\
        .replace("†", " ")\
        .replace("$", " ")\
        .replace("(", " ")\
        .replace(")", " ")\
        .replace("[", " ")\
        .replace("]", " ")\
        .replace("{", " ")\
        .replace("}", " ")\
        .replace("/", " ")\
        .replace("\\", " ")\
        .replace("<", " ")\
        .replace(">", " ")\
        .replace("^", " ")\
        .replace("-", " ")\
        .replace("–", "")\
        .replace("—", " ")\
        .replace("_", "")\
        .replace("–", "")\
        .replace("…", " ")\
        .replace("  ", " ")\
        .replace("॰", "")\
        .replace("ï", "i")\
        .replace("ü", "u")\
        .replace("ạ", "a")\
        .replace('̥', "")\
        .replace("'̆'", "")\
        .replace("ใ", "")\
        .replace("'̆'", "")\
        .replace("\xad", "")\
        .replace("\xa0", "")\
        .replace("\u0306", "")\
        .replace("&", "")\
        .replace("°", "")

    text = re.sub("^ *", "", text)
    text = re.sub(" $", "", text)

    errors = set([c for c in text if c not in allowed_characters])

    if len(errors) != 0:
        print(f"[bright_red]errors:{errors}", end=" ")
        unicode_errors = [ord(error) for error in errors]
        for error in unicode_errors:
            print("[bright_red]", end="")
            print("\\u{:04x}".format(error), end=" ")

    return text
