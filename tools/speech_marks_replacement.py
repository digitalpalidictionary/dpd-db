# replace sandhi in the text

import re

from tools.pali_alphabet import pali_alphabet
from tools.speech_marks import SpeechMarkManager


def replace_speech_marks(text: str, speech_marks_manager: SpeechMarkManager) -> str:
    """Replace Sandhi and hypenated words."""

    pali_alphabet_string = "".join(pali_alphabet)
    splits = re.split(f"([^{pali_alphabet_string}])", text)

    for i in range(len(splits)):
        word = splits[i]
        # Skip empty strings
        if not word:
            continue

        # Check variants in unified manager
        if speech_marks_manager.has_variants(word):
            variants = speech_marks_manager.get_variants(word)
            if variants:
                splits[i] = "//".join(variants)

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
