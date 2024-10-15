
import json
from tools.paths import ProjectPaths


def make_all_tipitaka_word_set():
    """Make a set of all words in every corpus."""

    pth = ProjectPaths()

    with open(pth.cst_wordlist) as f:
        cst_wordlist = set(json.load(f))
    
    with open(pth.bjt_wordlist) as f:
        bjt_wordlist = set(json.load(f))

    with open(pth.sya_wordlist) as f:
        sya_wordlist = set(json.load(f))

    with open(pth.sya_wordlist) as f:
        sc_wordlist = set(json.load(f))
    
    return cst_wordlist | bjt_wordlist | sya_wordlist | sc_wordlist
