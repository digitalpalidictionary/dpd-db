
from rich import print

def hk_translit(text: str):
    hk_translit_dict: dict[str, str] = {
        "A": "ā",
        "I": "ī",
        "U": "ū",
        "R": "ṛ",
        "RR": "ṝ",
        "lR": "ḷ",
        "lRR": "ḹ",
        "M": "ṃ",
        "H": "ḥ",
        "G": "ṅ",
        "J": "ñ",
        "T": "ṭ",
        "D": "ḍ",
        "N": "ṇ",
        "z": "ṣ",
        "S": "ś",}

    translit: str = str()
    for char in text:
        translit += hk_translit_dict.get(char, char)
    return translit


def slp1_translit(text: str):
    slp1_translit_dict: dict[str, str] = {
        "A": "ā",
        "I": "ī",
        "U": "ū",
        "f": "ṛ",
        "F": "ṝ",
        "x": "ḷ",
        "X": "ḹ",
        "E": "ai",
        "O": "au",
        "M": "ṃ",
        "H": "ḥ",
        "K": "kh",
        "G": "gh",
        "N": "ṅ",
        "C": "ch",
        "J": "jh",
        "Y": "ñ",
        "w": "ṭ",
        "W": "ṭh",
        "q": "ḍ",
        "Q": "ḍh",
        "R": "ṇ",
        "T": "th",
        "D": "dh",
        "P": "ph",
        "B": "bh",
        "S": "ś",
        "z": "ṣ",
        # "/": "\u0951",
        # "\\": "\u0952,",
        # "^": "\u1ce0",
        }

    translit: str = str()
    for char in text:
        translit += slp1_translit_dict.get(char, char)
    return translit

# with open("temp/translit.txt", "w") as file:
#     file.write(slp1_translit("aha/m, a\kzA, anu^"))
