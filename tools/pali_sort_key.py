"""Functions for sorting by Pāḷi alphabetical order."""

import re

letter_to_number = {
        "√": "00",
        "a": "01",
        "ā": "02",
        "i": "03",
        "ī": "04",
        "u": "05",
        "ū": "06",
        "e": "07",
        "o": "08",
        "k": "09",
        "kh": "10",
        "g": "11",
        "gh": "12",
        "ṅ": "13",
        "c": "14",
        "ch": "15",
        "j": "16",
        "jh": "17",
        "ñ": "18",
        "ṭ": "19",
        "ṭh": "20",
        "ḍ": "21",
        "ḍh": "22",
        "ṇ": "23",
        "t": "24",
        "th": "25",
        "d": "26",
        "dh": "27",
        "n": "28",
        "p": "29",
        "ph": "30",
        "b": "31",
        "bh": "32",
        "m": "33",
        "y": "34",
        "r": "35",
        "l": "36",
        "v": "37",
        "s": "38",
        "h": "39",
        "ḷ": "40",
        "ṃ": "41"
    }

sanksrit_letter_to_number = {
        "√": "00",
        "a": "01",
        "ā": "02",
        "i": "03",
        "ī": "04",
        "u": "05",
        "ū": "06",
        "ṛ": "07",
        "ṝ": "08",
        "ḷ": "09",
        "ḹ": "10",
        "e": "11",
        "ai": "12",
        "o": "13",
        "au": "14",
        "ḥ": "15",
        "ṃ": "16",
        "k": "17",
        "kh": "18",
        "g": "19",
        "gh": "20",
        "ṅ": "21",
        "c": "22",
        "ch": "23",
        "j": "24",
        "jh": "25",
        "ñ": "26",
        "ṭ": "27",
        "ṭh": "28",
        "ḍ": "29",
        "ḍh": "30",
        "ṇ": "31",
        "t": "32",
        "th": "33",
        "d": "34",
        "dh": "35",
        "n": "36",
        "p": "37",
        "ph": "38",
        "b": "39",
        "bh": "40",
        "m": "41",
        "y": "42",
        "r": "43",
        "l": "44",
        "v": "45",
        "ś": "46",
        "ṣ": "47",
        "s": "48",
        "h": "49",
    }


def pali_list_sorter(words: list[str] | set[str]) -> list:
    """Sort a list or a set of words in Pāḷi alphabetical order.
    Usage:
    pali_list_sorter(list_of_pali_words)"""

    if isinstance(words, set):
        words = list(words)

    if words is None:
        return []

    else:
        pattern = "|".join(key for key in letter_to_number.keys())

        def replace(match):
            return letter_to_number[match.group(0)]

        sorted_words = sorted(
            words, key=lambda word: re.sub(pattern, replace, word))

        return sorted_words


def pali_sort_key(word: str) -> str:
    """A key for sorting in Pāḷi alphabetical order."
    Usage:
    list = sorted(list, key=pali_sort_key)
    db = sorted(db, key=lambda x: pali_sort_key(x.lemma_1))
    df.sort_values(
        by="lemma_1", inplace=True, ignore_index=True,
        key=lambda x: x.map(pali_sort_key))"""

    pattern = '|'.join(re.escape(key) for key in letter_to_number.keys())

    def replace(match):
        return letter_to_number[match.group(0)]

    if isinstance(word, int):
        return word
    else:
        return re.sub(pattern, replace, word)


def sanskrit_sort_key(word: str) -> str:
    """A key for sorting in Sanskrit alphabetical order."
    Usage:
    list = sorted(list, key=pali_sort_key)
    db = sorted(db, key=lambda x: sanskrit_sort_key(x.lemma_1))
    df.sort_values(
        by="lemma_1", inplace=True, ignore_index=True,
        key=lambda x: x.map(sanskrit_sort_key))"""

    pattern = '|'.join(re.escape(key) for key in sanksrit_letter_to_number.keys())

    def replace(match):
        return sanksrit_letter_to_number[match.group(0)]

    if isinstance(word, int):
        return word
    else:
        return re.sub(pattern, replace, word)
