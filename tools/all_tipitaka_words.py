# -*- coding: utf-8 -*-

"""Make a combined set of every word in the CST, BJT, SYA and SC corpuses.
Used by the grammar and inflections build scripts in db/."""

import json

from tools.paths import ProjectPaths


def make_all_tipitaka_word_set():
    """Make a set of all words in every corpus."""

    pth = ProjectPaths()

    with open(pth.cst_wordlist, encoding="utf-8") as f:
        cst_wordlist = set(json.load(f))

    with open(pth.bjt_wordlist, encoding="utf-8") as f:
        bjt_wordlist = set(json.load(f))

    with open(pth.sya_wordlist, encoding="utf-8") as f:
        sya_wordlist = set(json.load(f))

    with open(pth.sya_wordlist, encoding="utf-8") as f:
        sc_wordlist = set(json.load(f))

    return cst_wordlist | bjt_wordlist | sya_wordlist | sc_wordlist


if __name__ == "__main__":
    print("saṃghabhedassa" in make_all_tipitaka_word_set())
