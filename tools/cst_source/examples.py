import re

from bs4 import element

from tools.cst_source.text_utils import clean_gatha
from tools.tokenizer import split_sentences


def _sibling_tag(x: element.Tag, forward: bool) -> element.Tag | None:
    """Nearest sibling tag, or None at the edge or at loose text (a verse boundary)."""
    sib = x.next_sibling if forward else x.previous_sibling
    while sib is not None and not isinstance(sib, element.Tag):
        if sib.text.strip():
            return None
        sib = sib.next_sibling if forward else sib.previous_sibling
    return sib


def _rend(x: element.Tag | None) -> str:
    return "" if x is None else str(x.get("rend", ""))


def find_verse_start(x: element.Tag) -> element.Tag:
    """Walk back to the first line of the verse that ``x`` belongs to."""

    # Some verses have no gatha1 (e.g. the Dhammapada uddāna), so a verse also
    # starts right after a gathalast or any non-verse element.
    start = x
    while _rend(start) != "gatha1":
        prev = _sibling_tag(start, forward=False)
        if prev is None or _rend(prev) not in ("gatha1", "gatha2", "gatha3"):
            break
        start = prev
    return start


def find_gatha_example(x: element.Tag) -> list[str]:
    """Find an example in a gāthā. Returns at most one example."""

    line = find_verse_start(x)
    example = clean_gatha(line.text)

    # A gatha1 met here is usually a mid-verse line marked oddly in the source,
    # so only a non-verse element ends a verse that has no gathalast.
    while _rend(line) != "gathalast":
        next_line = _sibling_tag(line, forward=True)
        rend = _rend(next_line)
        if next_line is None or rend not in ("gatha1", "gatha2", "gatha3", "gathalast"):
            break
        line = next_line
        text = clean_gatha(line.text)
        if rend == "gathalast":
            example += re.sub(",$", ".", text)
        else:
            example += text.replace(".", ",")

    # Every verse ends with a full stop, also one that stops early or is a
    # single line, where the "," from a ";" or a swapped "." would otherwise stay.
    example = re.sub(",$", ".", example)

    if example:
        return [example]
    return []


def find_sentence_example(text: str, text_to_find: str) -> list[str]:
    examples: list[str] = []
    sentences = split_sentences(text)
    for i, sentence in enumerate(sentences):
        if re.findall(text_to_find, sentence):
            prev_sentence = sentences[i - 1] if i > 0 else ""
            next_sentence = sentences[i + 1] if i < len(sentences) - 1 else ""
            examples.append(f"{prev_sentence}{sentence}{next_sentence}")
    return examples
