"""Task 2.2: write six new prompts to sample_prompts.md, check the leak
guard, and compare prompt lengths old vs new."""

import sys

from sqlalchemy import select

from db.models import DpdHeadword

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from context import EVAL_DIR, db, g_prompts, k_prompts, words  # type: ignore  # noqa: E402

w = words()
picks = [("G", e) for e in w["G"] if e["word"] in ("vīraka", "jhāpaye", "dharaṇīruhaṃ")]
picks += [("K", e) for e in w["K"] if e["word"] in ("revatīvimānaṃ", "jinapabhuttamaṃ", "kapirājacariyā")]

out: list[str] = ["# Sample new prompts (task 2.2)\n"]
fixed_done = False
for set_name, entry in picks:
    old, new, _ = (g_prompts if set_name == "G" else k_prompts)(entry)
    fixed, word_part = new.split("\n---\n", 1)
    if not fixed_done:
        out.append("## Fixed part (the same for every word)\n\n````text\n" + fixed + "\n````\n")
        fixed_done = True
    leak = ""
    if set_name == "G":
        golds = [hw.lemma_1 for i in entry["gold_ids"] if (hw := db.get(DpdHeadword, i))]
        leaked = [g for g in golds if f'"lemma_1": "{g}"' in word_part]
        leak = f" — gold {golds}, leaked in related: {leaked or 'none'}"
    out.append(
        f"## {set_name}: {entry['word']}{leak}\n\nold prompt {len(old)} chars (~{len(old)//4} tokens), "
        f"new prompt {len(new)} chars (~{len(new)//4} tokens), of which word part {len(word_part)} chars\n\n"
        f"````text\n---\n{word_part}````\n"
    )
    print(set_name, entry["word"], len(old), len(new), len(word_part), leak)
(EVAL_DIR / "sample_prompts.md").write_text("\n".join(out), encoding="utf-8")

# Fixed-part leak scan: rules and example must not name any test word or
# any gold answer value (the value lists are the dictionary itself, so skip them).
import re  # noqa: E402

rules = fixed.split("# Real dictionary values", 1)[0]
tokens = set(re.findall(r"[a-zāīūṅñṭḍṇḷṃ√]+", rules))
hits: list[str] = []
for e in w["K"]:
    if e["word"] in tokens:
        hits.append(f"K word {e['word']}")
for e in w["G"]:
    if e["word"] in tokens:
        hits.append(f"G word {e['word']}")
    for i in e["gold_ids"]:
        hw = db.get(DpdHeadword, i)
        if hw is None:
            continue
        lemma = re.sub(r" \d.*$", "", hw.lemma_1)
        if lemma in tokens:
            hits.append(f"G gold lemma {lemma} ({e['word']})")
        for field in ("construction", "family_compound", "family_root", "root_base"):
            value = getattr(hw, field).split("\n")[0]
            if " " in value and value in rules:
                hits.append(f"G gold {field} '{value}' ({e['word']})")
print("fixed-part leaks:", hits or "none")
