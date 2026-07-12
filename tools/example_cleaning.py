"""Clean example and commentary passages: apply speech mark variants,
normalize niggahīta and bold-tag punctuation, and remove bracketed content.
Used by gui2 field cleaning, exporter/analysis and scripts/fix."""

import re

from tools.pali_alphabet import pali_alphabet
from tools.speech_marks import SpeechMarkManager


def clean_speech_marks(
    text: str,
    speech_marks_manager: SpeechMarkManager,
) -> str:
    pali_alphabet_string = "".join(pali_alphabet)
    splits = re.split(f"([^{pali_alphabet_string}])", text)

    for i in range(len(splits)):
        word = splits[i]
        if not word:
            continue

        variants = speech_marks_manager.get_variants(word)
        if variants:
            splits[i] = "//".join(variants)

    return "".join(splits)


def clean_text(text: str) -> str:
    # replace ṁ with ṃ
    text = text.replace("ṁ", "ṃ")
    # fix bold 'ti
    text = text.replace("</b>ti", "</b>'ti")
    # fix bold 'ti
    text = text.replace("</b>nti", "n</b>'ti")
    # fix 'n</b>'ti
    text = text.replace("'n</b>'ti", "n</b>'ti")
    # fix bold comma
    text = text.replace(",</b>", "</b>,")
    # fix bold stop
    text = text.replace(".</b>", "</b>.")
    # fix bold quote
    text = text.replace("'</b>'", "</b>'")
    # fix 'tipi
    text = text.replace("'tipi", "'ti'pi")
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


def clean_commentary(
    text: str,
    speech_marks_manager: SpeechMarkManager,
) -> str:
    text = clean_speech_marks(text, speech_marks_manager)
    text = clean_text(text)
    return text


def remove_brackets(text: str) -> str:
    """Remove all content within square brackets [like this]."""
    text = re.sub(r"[^\S\n]*\[[^]]*\][^\S\n]*", " ", text)
    text = re.sub(r"[^\S\n]+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])[^\S\n]*(?=[^\s\d])", r"\1 ", text)
    text = re.sub(r"[^\S\n]+\n", "\n", text)
    text = re.sub(r"\n[^\S\n]+", "\n", text)
    return text.strip()


def remove_bold_tags(text: str) -> str:
    """Remove <b> and </b> tags from text."""
    return text.replace("<b>", "").replace("</b>", "")


def clean_example(
    text: str,
    speech_marks_manager: SpeechMarkManager,
) -> str:
    text = clean_speech_marks(text, speech_marks_manager)
    text = clean_text(text)
    return text
