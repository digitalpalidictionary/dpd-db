# replace sandhi in the text

import re

from tools.pali_alphabet import pali_alphabet


def replace_sandhi(text: str, sandhi_dict: dict, hyphenations_dict: dict) -> str:
    """Replace Sandhi and hypenated words."""

    pali_alphabet_string = "".join(pali_alphabet)
    splits = re.split(f"([^{pali_alphabet_string}])", text)

    for i in range(len(splits)):
        word = splits[i]
        if word in sandhi_dict:
            splits[i] = "//".join(sandhi_dict[word]["contractions"])

        if word in hyphenations_dict:
            splits[i] = hyphenations_dict[word]

    text = "".join(splits)

    # replace ṁ with ṃ
    text = text.replace("ṁ", "ṃ")
    # fix bold 'ti
    text = text.replace("</b>ti", "</b>'ti")
    # fix bold 'ti
    text = text.replace("</b>nti", "n</b>'ti")
    # fix bold comma
    text = text.replace(",</b>", "</b>,")
    # fix bold stop
    text = text.replace(".</b>", "</b>.")
    # fix bold quote
    text = text.replace("'</b>'", "</b>'")
    # fix 'tipi
    text = text.replace("'tipi", "'ti'pi")
    # remove [...]
    text = re.sub(r"\[[^]]*\]", "", text)
    # remove double spaces
    text = re.sub(" +", " ", text)
    # remove digits in front
    text = re.sub(r"^\d*\. ", "", text)
    # remove space comma
    text = text.replace(" ,", ",")
    # remove space fullstop
    text = text.replace(" .", ".")
    # remove spaces front n back
    text = text.strip()

    return text
