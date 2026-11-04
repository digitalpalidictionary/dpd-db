"""Task 4.2: build artifacts/spot_check.html, a static side-by-side page of 20
words (10 G, 10 K): sentences sent, old answer, new answer, and the dictionary
entry for G words.

cd <repo> && uv run kamma/threads/20261104_pass1_auto_prompt/artifacts/eval/spot_check.py"""

import html
import json
import random
import sys

from sqlalchemy import select

from db.models import DpdHeadword
from gui2.books import sutta_central_books
from gui2.pass1_context import ANSWER_KEYS, Sentence

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from context import EVAL_DIR, db, g_prompts, k_prompts, words  # type: ignore  # noqa: E402
from saved_prompt import parse_saved_prompt, read_saved_prompt  # type: ignore  # noqa: E402

MODEL = "deepseek-v4-flash"
SCORED = {"lemma_1", "pos", "root_key", "family_root", "family_compound", "construction", "stem", "pattern"}
K_PER_BOOK = {"Vv": 2, "Pv": 2, "Ap-i": 2, "Ap-ii": 2, "Bv": 1, "Cp": 1}

rng = random.Random(20261104)
all_words = words()
g_with = [e for e in all_words["G"] if e["had_sentence"]]
g_without = [e for e in all_words["G"] if not e["had_sentence"]]
g_pick = rng.sample(g_with, 5) + rng.sample(g_without, 5)
k_pick = [
    e
    for book, n in K_PER_BOOK.items()
    for e in rng.sample([x for x in all_words["K"] if x["book"] == book], n)
]


def answer(set_name: str, version: str, word: str) -> dict:
    text = (EVAL_DIR / "raw" / set_name / MODEL / version / f"{word}.txt").read_text(encoding="utf-8")
    return json.loads(text.replace("```json\n", "").replace("```", "").strip())


def gold_values(hw: DpdHeadword) -> dict[str, str]:
    values = {key: str(getattr(hw, key, "") or "") for key in ANSWER_KEYS if key != "comment"}
    values["lemma_2"] = hw.lemma_2 or ""
    values["meaning_2"] = hw.meaning_combo
    return values


def norm(value: str) -> str:
    return value.strip()


def sentences_html(title: str, sentences: list[Sentence]) -> str:
    if not sentences:
        return f'<div class="sent"><h4>{title}</h4><p class="none">no sentence</p></div>'
    items = "".join(
        f"<li><span class='pali'>{html.escape(p)}</span><br><span class='en'>{html.escape(e)}</span></li>"
        for p, e in sentences
    )
    return f'<div class="sent"><h4>{title}</h4><ol>{items}</ol></div>'


def card(set_name: str, entry: dict) -> str:
    word = entry["word"]
    old = answer(set_name, "old", word)
    new = answer(set_name, "new", word)
    if set_name == "G":
        old_sents, _ = parse_saved_prompt(read_saved_prompt(word))
        _, _, new_sents = g_prompts(entry)
        golds = list(db.scalars(select(DpdHeadword).where(DpdHeadword.id.in_(entry["gold_ids"]))))

        def score(hw: DpdHeadword) -> int:
            g = gold_values(hw)
            return sum(norm(str(new.get(k, ""))) == norm(g[k]) for k in SCORED if k != "lemma_1")

        gold = gold_values(max(golds, key=score)) if golds else None
        if gold is not None:
            lemma_clean = max(golds, key=score).lemma_clean
        tag = "had a sentence before" if entry["had_sentence"] else "had NO sentence before"
    else:
        book = entry["book_key"]
        sc = sutta_central_books[book].word_dict.get(word, []) if book in sutta_central_books else []
        old_sents = [(s.pali, s.english) for s in sc]
        _, _, new_sents = k_prompts(entry)
        gold = None
        tag = "not in DPD yet"

    head = "<tr><th>field</th><th>old prompt</th><th>new prompt</th>"
    head += "<th>dictionary</th></tr>" if gold else "</tr>"
    rows = []
    for key in ANSWER_KEYS:
        o, n = str(old.get(key, "")), str(new.get(key, ""))
        cells = [o, n]
        classes = ["", ""]
        if gold is not None and key in SCORED:
            target = lemma_clean if key == "lemma_1" else gold[key]
            classes = ["hit" if norm(v) == norm(target) else "miss" for v in cells]
        row = f"<td class='key'>{key}</td>" + "".join(
            f"<td class='{c}'>{html.escape(v)}</td>" for v, c in zip(cells, classes)
        )
        if gold is not None:
            row += f"<td class='gold'>{html.escape(gold.get(key, ''))}</td>"
        rows.append(f"<tr>{row}</tr>")
    return f"""
<section class="card">
  <h2>{html.escape(word)} <span class="tag">{set_name} · {html.escape(entry['book'])} · {tag}</span></h2>
  <div class="sents">{sentences_html("old prompt sentences", old_sents)}{sentences_html("new prompt sentences", new_sents)}</div>
  <div class="scroll"><table>{head}{"".join(rows)}</table></div>
</section>"""


cards = [card("G", e) for e in g_pick] + [card("K", e) for e in k_pick]

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pass1 Spot Check</title>
<style>
:root {{ --bg:#fdfcf9; --fg:#222; --muted:#666; --line:#ddd; --card:#fff; --hit:#dff3df; --miss:#fbe1e1; --gold:#f4efe2; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#1b1b1b; --fg:#e8e8e8; --muted:#aaa; --line:#3a3a3a; --card:#242424; --hit:#21402a; --miss:#4a2526; --gold:#3a3426; }} }}
:root[data-theme="dark"] {{ --bg:#1b1b1b; --fg:#e8e8e8; --muted:#aaa; --line:#3a3a3a; --card:#242424; --hit:#21402a; --miss:#4a2526; --gold:#3a3426; }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, sans-serif; margin:0 auto; padding:16px; max-width:1200px; }}
h1 {{ font-size:1.4em; }} .intro {{ color:var(--muted); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 16px; margin:20px 0; }}
.card h2 {{ margin:0 0 8px; font-size:1.2em; }} .tag {{ font-size:.7em; color:var(--muted); font-weight:normal; }}
.sents {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
@media (max-width:700px) {{ .sents {{ grid-template-columns:1fr; }} }}
.sent h4 {{ margin:4px 0; font-size:.85em; color:var(--muted); }} .sent ol {{ margin:0; padding-left:20px; }}
.sent li {{ margin-bottom:6px; }} .pali {{ font-style:italic; }} .en {{ color:var(--muted); }} .none {{ color:var(--muted); margin:0; }}
.scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; margin-top:10px; font-size:.9em; }}
th, td {{ border:1px solid var(--line); padding:4px 8px; text-align:left; vertical-align:top; white-space:pre-wrap; }}
td.key {{ color:var(--muted); white-space:nowrap; }} td.hit {{ background:var(--hit); }} td.miss {{ background:var(--miss); }} td.gold {{ background:var(--gold); }}
</style></head><body>
<h1>Pass1 Auto spot check — old prompt vs new prompt (DeepSeek flash)</h1>
<p class="intro">20 words: 10 already in DPD (G, with the dictionary entry), 10 not yet in DPD (K). Green / red marks the 8 auto-scored fields against the dictionary. Meanings and grammar are for you to judge.</p>
{"".join(cards)}
</body></html>
"""

out = EVAL_DIR.parent / "spot_check.html"
out.write_text(page, encoding="utf-8")
print(f"wrote {out} with {len(cards)} words: {[e['word'] for e in g_pick + k_pick]}")
