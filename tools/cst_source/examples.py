import re
import time

from bs4 import element
from rich import print

from tools.cst_source.text_utils import clean_gatha
from tools.tokenizer import split_sentences


def find_gatha_example(
    x: element.Tag | element.NavigableString | None, text_to_find: str
) -> list[str]:
    """Find an example in a gāthā. Returns at most one example."""

    example = ""

    start_time = time.time()
    while x is not None:
        if x.text == "\n":
            x = x.previous_sibling
            continue
        if x["rend"] == "gatha1":
            break
        if x["rend"] in ("gatha2", "gatha3", "gathalast"):
            x = x.previous_sibling
            continue
        if time.time() - start_time > 1:
            print(f"[bright_red]{text_to_find} [red]is stuck in a loop")
            x = None
            break

    if x is None:
        return []

    text = clean_gatha(x.text)
    example += text

    while True:
        try:
            if x is not None:
                x = x.next_sibling
                if x.text == "\n":
                    pass
                elif x["rend"] == "gatha2" or x["rend"] == "gatha3":
                    text = clean_gatha(x.text)
                    text = text.replace(".", ",")
                    example += text
                elif x["rend"] == "gathalast":
                    text = clean_gatha(x.text)
                    text = re.sub(",$", ".", text)
                    example += text
                    break
            else:
                break
        except AttributeError as e:
            print(f"[red]{e}")
            print(text_to_find)
            print(x)
            break

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
