"""A text cleaning machine."""

import re
from rich import print
from tools.unicode_char import unicode_char

def clean_machine(text: str, niggahita="ṃ", remove_hyphen=True) -> str:
    
    """
    Return clean text with only allowable characters
    - optionally change the niggahita character
    - optionally keep the hyphen
    """

    allowed_characters = "aāiīuūeokgṅcjñṭḍṇtdnpbmyrlsvhḷṃṁ\n xfśṣǣæwqḥṛz"

    text = text.lower()
    text = re.sub(r"\d", "", text)
    text = re.sub(r"\t", "", text)
    text = re.sub(r"\n", r" \n", text)

    if niggahita == "ṃ":
        text = text.replace("ṁ", "ṃ")

    text = text.replace(".", " ")\
        .replace("<b>", " ")\
        .replace("</b>", " ")\
        .replace(",", " ")\
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
        .replace("+", " ")\
        .replace("*", "")\
        .replace("=", " ")\
        .replace("~", " ")\
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
        .replace(" - ", " ")\
        .replace("–", " ")\
        .replace("—", " ")\
        .replace("t_", "v")\
        .replace("_", "")\
        .replace("…", " ")\
        .replace("  ", " ")\
        .replace("॰", " ")\
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
        .replace("°", "")\
        .replace("ġ", "g")\
        .replace("ṟ", "r")\
        .replace("ṉ", "n")\
        .replace("ẏ", "y")\
        .replace("ḥ", "")\
        .replace("ṛ", "")\
        .replace("\u0308", "")\
        .replace("\u035f", "")\
        .replace("\u0324", "")\
        .replace("--", " ")\
        .replace("♦", " ")

    
    if remove_hyphen:
        text = text.replace("-", "")\

    text = re.sub("^ *", "", text)
    text = re.sub(" $", "", text)

    if remove_hyphen == False:
        allowed_characters += "-"
    errors = set([c for c in text if c not in allowed_characters])


    if len(errors) != 0:
        print(f"[bright_red]errors:{errors}", end=" ")
        unicode_errors = [unicode_char(error) for error in errors]
        for error in unicode_errors:
            print(f"[bright_red]{error}", end=" ")

    return text

# clean_machine("½¾")