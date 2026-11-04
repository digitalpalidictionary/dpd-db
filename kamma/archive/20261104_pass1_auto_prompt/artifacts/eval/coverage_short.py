"""Task 1.4 follow-up: PEU matches for short missing words, and Cp with its auto keys ignored."""

import random

from tools.epitaka_sentences import epitaka_word_dict, peu_entries

from common import TARGET_BOOKS, MissingChecker, cst_file_stems  # type: ignore

checker = MissingChecker()
short: list[tuple[str, int, str]] = []
for ep_book, (book_key, cst_books) in TARGET_BOOKS.items():
    for w in checker.missing_words(book_key, cst_books):
        if len(w) <= 6:
            for cut in range(0, 4):
                hits = peu_entries(w, max_cut=cut)
                if hits:
                    if cut >= 2:
                        short.append((w, cut, hits[0][:80]))
                    break
print(len(short), "short words (<=6 letters) matched at cut 2 or 3")
random.seed(1)
for w, cut, hit in random.sample(short, min(20, len(short))):
    print(f"- {w} | cut {cut} | {hit}")

auto = checker.auto_keys("cp")
from tools.cst_sc_text_sets import make_cst_text_list  # noqa: E402

cp_words = [w for w in make_cst_text_list(["kn13"]) if checker.is_missing(w, set())]
ep = epitaka_word_dict(cst_file_stems(["kn13"]))
print("\nCp missing words if pass1_auto_cp.json is ignored:", len(cp_words))
print("of these, in pass1_auto_cp.json:", sum(1 for w in cp_words if w in auto))
print("with >=1 ePitaka sentence:", sum(1 for w in cp_words if ep.get(w)))
