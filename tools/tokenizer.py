from rich import print


def split_sentences(text: str) -> list[str]:
    """Split a sentence on all final punctuation marks,
    but never when there is an open bracket."""

    sentences = []
    split_list = [". ", "! ", "? ", "; "]
    bracket_is_closed: bool = True

    i = 0
    while len(text) > 0:
        if i == len(text):
            sentences.append(text[: i + 1])
            break
        if text[i] == "(":
            bracket_is_closed = False
        if text[i] == ")":
            bracket_is_closed = True
        if text[i : i + 2] in split_list:
            if bracket_is_closed:
                sentences.append(text[: i + 2])
                text = text[i + 2 :]
                i = 0
                continue
        i += 1
    return sentences


dirty_clean_dict: dict[str, str] = {
    ";": "",
    ",": "",
    " '": " ",
    "!": "",
    "%": "",
    "&": "",
    "(": "",
    ")": "",
    "*": "",
    "-": "",
    ".": "",
    "/": "",
    ";": "",
    "=": "",
    "?": "",
    "…": "",
    "√": "",
}


def remove_dirty_characters(text):
    for dirty, clean in dirty_clean_dict.items():
        text = text.replace(dirty, clean)
    return text


def remove_dirty_characters_keep_dash(text):
    dirty_clean_dict_keep_dash = dirty_clean_dict.copy()
    del dirty_clean_dict_keep_dash["-"]  # remove current dash replacement
    dirty_clean_dict_keep_dash["-"] = " "  # replace dash with space
    for dirty, clean in dirty_clean_dict_keep_dash.items():
        text = text.replace(dirty, clean)
    return text


def split_words(text: str) -> list[str]:
    text = remove_dirty_characters(text)
    return text.split()


def split_words_keep_dash(text: str) -> list[str]:
    text = remove_dirty_characters_keep_dash(text)
    return text.split()


if __name__ == "__main__":
    example = "saṅkhepato hi pañcupādānakkhandhā āsīvisūpame (saṃ. ni. 4.238) vuttanayena ukkhittāsikapaccatthikato, bhārasuttavasena (saṃ. ni. 3.22) bhārato, khajjanīyapariyāyavasena (saṃ. ni. 3.79) khādakato, yamakasuttavasena (saṃ. ni. 3.85) aniccadukkhānattasaṅkhatavadhakato daṭṭhabbā. vitthārato panettha pheṇapiṇḍo viya rūpaṃ daṭṭhabbaṃ, parimaddanāsahanato. udakapubbuḷaṃ"
    # x = split_sentences(example)

    text = "can i have an example of a sentence with one's and twos and 12ths ant 47th"
    text = split_words(example)
    print(text)
