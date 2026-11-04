"""Task 2.1: build_old_prompt must rebuild saved old prompts exactly."""

import json
import sys

from gui2.pass1_context import build_old_prompt

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from saved_prompt import parse_saved_prompt, read_saved_prompt  # type: ignore  # noqa: E402

words = json.load(open("kamma/threads/20261104_pass1_auto_prompt/artifacts/eval/words.json"))["G"]
with_s = [g["word"] for g in words if g["had_sentence"]][:2]
without = [g["word"] for g in words if not g["had_sentence"]][:1]
same = 0
for w in with_s + without + [g["word"] for g in words]:
    saved = read_saved_prompt(w)
    sentences, related = parse_saved_prompt(saved)
    ok = build_old_prompt(w, sentences, related) == saved
    same += ok
    if w in with_s + without:
        print(f"{w}: sentences={len(sentences)} related={len(related)} identical={ok}")
print(f"all 50 G words: {same - 3} of 50 identical")
