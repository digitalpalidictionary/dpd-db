"""Parse a saved old Pass1 Auto prompt (temp/prompts/pass1/{word}_prompt)
back into its sentences and related entries."""

import re
from pathlib import Path

PROMPT_DIR = Path("temp/prompts/pass1")


def read_saved_prompt(word: str) -> str:
    return (PROMPT_DIR / f"{word}_prompt").read_text(encoding="utf-8")


def parse_saved_prompt(prompt: str) -> tuple[list[tuple[str, str]], list[str]]:
    sent_block = prompt.split("## Sentences: \n", 1)[1].split("\n\n## Related dictionary entries:\n", 1)[0]
    sentences: list[tuple[str, str]] = []
    for m in re.finditer(r"(\d+)\. Pāḷi : (.*?)\n\1\. English: (.*?)\n(?=\n\d+\. Pāḷi : |$)", sent_block, re.S):
        sentences.append((m.group(2), m.group(3)))
    rel_block = prompt.split("## Related dictionary entries:\n", 1)[1].split("\n---        \n", 1)[0]
    related = [] if not rel_block else [e.removeprefix("- ") for e in re.split(r"\n(?=- lemma_1: )", rel_block)]
    return sentences, related
