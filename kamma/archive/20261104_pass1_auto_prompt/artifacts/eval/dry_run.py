"""Task 2.3: send the new prompt for 5 K words (one each from Vv, Pv, Ap-i,
Ap-ii, Bv) to one model, save the raw answers, check every answer is JSON
with exactly the 14 expected keys and string values.

uv run kamma/threads/20261104_pass1_auto_prompt/artifacts/eval/dry_run.py deepseek deepseek-v4-flash
uv run kamma/threads/20261104_pass1_auto_prompt/artifacts/eval/dry_run.py zai glm-5.3-flash"""

import json
import sys

from gui2.pass1_context import ANSWER_KEYS, SYSTEM_PROMPT
from tools.ai_manager import AIManager

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from context import EVAL_DIR, k_prompts, words  # type: ignore  # noqa: E402

provider, model = sys.argv[1], sys.argv[2]
out_dir = EVAL_DIR / "raw" / "dry" / model
out_dir.mkdir(parents=True, exist_ok=True)

picked: list[dict] = []
for book in ("Vv", "Pv", "Ap-i", "Ap-ii", "Bv"):
    picked.append(next(e for e in words()["K"] if e["book"] == book))

ai = AIManager()
ok = 0
for entry in picked:
    word = entry["word"]
    raw_file = out_dir / f"{word}.txt"
    if raw_file.exists():
        text = raw_file.read_text(encoding="utf-8")
        status = "(saved earlier)"
    else:
        _, new, _ = k_prompts(entry)
        response = ai.request(
            prompt=new, prompt_sys=SYSTEM_PROMPT, provider_preference=provider, model=model
        )
        status = response.status_message
        if response.content is None:
            print(f"{word}: NO ANSWER | {status}")
            continue
        text = response.content
        raw_file.write_text(text, encoding="utf-8")
    cleaned = text.replace("```json\n", "").replace("```", "")
    try:
        answer = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"{word}: NOT JSON ({e}) | {status}")
        continue
    keys_ok = list(answer) == list(ANSWER_KEYS)
    strings_ok = all(isinstance(v, str) for v in answer.values())
    ok += keys_ok and strings_ok
    print(f"{word}: keys exact and in order={keys_ok} all strings={strings_ok} | {status}")
print(f"{provider}/{model}: {ok} of {len(picked)} answers valid")
