"""Task 3.1: send the old and new prompt for every test word to DeepSeek flash
and save the raw answers. Files that exist are skipped, so a rerun resumes.

Raw layout: raw/{set}/{model}/{version}/{word}.txt  (set = G or K, version = old or new)

cd <repo> && uv run kamma/threads/20261104_pass1_auto_prompt/artifacts/eval/run.py [limit_per_set]
The optional limit runs only the first N words of each set (use 1 for a 4-file trial)."""

import sys
from concurrent.futures import ThreadPoolExecutor

from icecream import ic

from gui2.pass1_context import SYSTEM_PROMPT, SYSTEM_PROMPT_OLD
from tools.ai_manager import AIManager

sys.path.insert(0, "kamma/threads/20261104_pass1_auto_prompt/artifacts/eval")
from context import EVAL_DIR, g_prompts, k_prompts, words  # type: ignore  # noqa: E402

PROVIDER = "deepseek"
MODEL = "deepseek-v4-flash"
WORKERS = 4

limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

# Build every prompt first: the db session in context.py is not thread-safe.
jobs: list[tuple[str, str, str, str, str]] = []  # (set, version, word, prompt, system)
for set_name, build in (("G", g_prompts), ("K", k_prompts)):
    entries = words()[set_name][:limit]
    for entry in entries:
        old, new, _ = build(entry)
        for version, prompt, system in (
            ("old", old, SYSTEM_PROMPT_OLD),
            ("new", new, SYSTEM_PROMPT),
        ):
            out = EVAL_DIR / "raw" / set_name / MODEL / version / f"{entry['word']}.txt"
            if not out.exists():
                jobs.append((set_name, version, entry["word"], prompt, system))
ic(len(jobs))

ai = AIManager()


def send(job: tuple[str, str, str, str, str]) -> tuple[str, str] | None:
    set_name, version, word, prompt, system = job
    out_dir = EVAL_DIR / "raw" / set_name / MODEL / version
    out_dir.mkdir(parents=True, exist_ok=True)
    response = ai.request(
        prompt=prompt, prompt_sys=system, provider_preference=PROVIDER, model=MODEL
    )
    if response.content is None:
        return f"{set_name}/{version}/{word}", response.status_message
    (out_dir / f"{word}.txt").write_text(response.content, encoding="utf-8")
    return None


with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    failures = [f for f in pool.map(send, jobs) if f]

total = sum(1 for _ in (EVAL_DIR / "raw").glob(f"[GK]/{MODEL}/*/*.txt"))
print(f"raw files on disk: {total}")
for name, error in failures:
    print(f"FAILED {name}: {error}")
print(f"{len(failures)} failures")
