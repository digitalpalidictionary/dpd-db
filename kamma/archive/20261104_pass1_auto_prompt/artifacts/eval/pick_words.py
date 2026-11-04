"""Task 1.5: pick Set G (50 gold words) and Set K (50 keep words) into words.json."""

import json
import random
import re
from collections import Counter
from pathlib import Path

from sqlalchemy import select

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.cst_sc_text_sets import make_cst_text_list
from tools.paths import ProjectPaths

from common import EVAL_DIR, TARGET_BOOKS, MissingChecker  # type: ignore

random.seed(20261104)
PROMPT_DIR = Path("temp/prompts/pass1")
VERSE_BOOKS = {"cp": ["kn13"], "th": ["kn8"], "thi": ["kn9"], "ja": ["kn14"], "dhp": ["kn2"], "snp": ["kn5"]}

# --- Set G ---
verse_words = {b: set(make_cst_text_list(c, show_errors=False)) for b, c in VERSE_BOOKS.items()}

db = get_db_session(ProjectPaths().dpd_db_path)
lookup: dict[str, list[int]] = {}
for row in db.execute(select(Lookup)).scalars():
    ids = row.headwords_unpack
    if ids:
        lookup[row.lookup_key] = ids
db.close()


def has_sentence(prompt: str) -> bool:
    m = re.search(r"## Sentences: ?\n(.*?)\n## Related", prompt, re.S)
    return bool(m and m.group(1).strip())


pool: list[dict] = []
for p in PROMPT_DIR.glob("*_prompt"):
    word = p.name.removesuffix("_prompt")
    resp = PROMPT_DIR / f"{word}_response"
    if word not in lookup or not resp.exists():
        continue
    try:
        json.loads(resp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        continue
    prompt = p.read_text(encoding="utf-8")
    if "## Word in the text" not in prompt:
        continue
    book = next((b for b, ws in verse_words.items() if word in ws), None)
    pool.append(
        {"word": word, "book": book, "had_sentence": has_sentence(prompt), "gold_ids": lookup[word]}
    )

print("gold pool:", len(pool), "| in verse books:", sum(1 for g in pool if g["book"]))
print("verse pool with/without sentence:", Counter(g["had_sentence"] for g in pool if g["book"]))

verse = [g for g in pool if g["book"]]
random.shuffle(verse)
set_g = [g for g in verse if not g["had_sentence"]][:25]
set_g += [g for g in verse if g["had_sentence"]][: 50 - len(set_g)]
if len(set_g) < 50:
    rest = [g for g in pool if not g["book"]]
    random.shuffle(rest)
    set_g += rest[: 50 - len(set_g)]

# --- Set K ---
checker = MissingChecker()
per_book = {"Vv": 8, "Pv": 8, "Ap-i": 8, "Ap-ii": 8, "Bv": 9, "Cp": 9}
set_k: list[dict] = []
taken: set[str] = set()
for ep_book, (book_key, cst_books) in TARGET_BOOKS.items():
    if ep_book == "Cp":
        # Every Cp missing word already has an old answer; ignore that file here.
        cands = [w for w in make_cst_text_list(cst_books, show_errors=False) if checker.is_missing(w, set())]
    else:
        cands = checker.missing_words(book_key, cst_books)
    cands = [w for w in cands if w not in taken]
    for w in random.sample(cands, per_book[ep_book]):
        taken.add(w)
        set_k.append({"word": w, "book": ep_book, "book_key": book_key, "cst_books": cst_books})

out = {"G": set_g, "K": set_k}
(EVAL_DIR / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("G:", len(set_g), Counter(g["book"] for g in set_g), Counter(g["had_sentence"] for g in set_g))
print("K:", len(set_k), Counter(k["book"] for k in set_k))
