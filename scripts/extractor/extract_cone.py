#!/usr/bin/env python3

import signal
import time
from pathlib import Path

from tools.ai_open_router import OpenRouterManager
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.goldendict_tools import open_in_goldendict

from scripts.extractor._signal_handler import state, signal_handler
from scripts.extractor._ai_extraction import extract_with_ai
from scripts.extractor._pos_mapping import map_pos_to_dpd
from scripts.extractor._read_cone import get_cone_html_entries
from scripts.extractor._load_cone import load_cone_dictionary, get_cone_headwords
from scripts.extractor._word_list import prepare_word_list
from scripts.extractor._output import write_to_tsv, write_no_source
from scripts.extractor._prompts import CONE_PROMPT

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

MODEL = "deepseek/deepseek-v3.2"

CONE_POS_MAPPING = {
    "ind": "ind",
    "ind.": "ind",
    "pron1pers": "pron",
    "pron.1pers.": "pron",
    "pr3sg": "pr",
    "pr.3sg.": "pr",
    "pr. 3 sg.": "pr",
    "pr 3 sg": "pr",
    "pr1sg": "pr",
    "pr.1sg.": "pr",
    "pr. 1 sg.": "pr",
    "pr 1 sg": "pr",
    "caus": "pr",
    "caus.": "pr",
    "caus3sg": "pr",
    "caus.3sg.": "pr",
    "caus. 3 sg.": "pr",
    "caus 3 sg": "pr",
    "caus. of": "pr",
    "v": "pr",
    "v.": "pr",
    "3sg": "pr",
    "3 sg": "pr",
    "3sg.": "pr",
    "3 sg.": "pr",
    "pass": "pr",
    "pass.": "pr",
    "pass3sg": "pr",
    "pass.3sg.": "pr",
    "pass. 3 sg.": "pr",
    "pass 3 sg": "pr",
    "3. sg. pass.": "pr",
    "3.": "pr",
    "aor3sg": "aor",
    "aor.3sg.": "aor",
    "aor. 3 sg.": "aor",
    "aor 3 sg": "aor",
    "aor1sg": "aor",
    "aor.1sg.": "aor",
    "aor. 1 sg.": "aor",
    "aor 1 sg": "aor",
    "aor3pl": "aor",
    "aor.3pl.": "aor",
    "aor. 3 pl.": "aor",
    "aor 3 pl": "aor",
    "opt1sg": "opt",
    "opt.1sg.": "opt",
    "opt. 1 sg.": "opt",
    "opt 1 sg": "opt",
    "opt3sg": "opt",
    "opt.3sg.": "opt",
    "opt. 3 sg.": "opt",
    "opt 3 sg": "opt",
    "fut3sg": "fut",
    "fut.3sg.": "fut",
    "fut. 3 sg.": "fut",
    "fut 3 sg": "fut",
    "absol": "abs",
    "absol.": "abs",
}


def connect_to_openrouter():
    pr.green("Connecting to OpenRouter")
    manager = OpenRouterManager()
    if manager.client:
        pr.yes("ok")
    else:
        pr.error("failed")
    return manager


def process_word(word, cone_dict, manager, output_path):
    entries = get_cone_html_entries(cone_dict, word)
    if not entries:
        pr.no("no source")
        write_no_source(output_path, word)
        return False

    all_meanings = []
    dpd_pos = None

    for homonym_num, html in entries:
        word_parentheses = f"{word[:4]}({word[4:]})" if len(word) > 4 else word
        prompt_data = {"word": word, "html": html, "word_parentheses": word_parentheses}
        result = extract_with_ai(
            manager,
            word,
            html,
            MODEL,
            CONE_PROMPT,
            rate_limit=3.0,
            prompt_data=prompt_data,
        )

        if result:
            cone_pos, meaning = result
            if cone_pos == "NOT_FOUND":
                continue
            if dpd_pos is None:
                dpd_pos = map_pos_to_dpd(cone_pos, word, CONE_POS_MAPPING)
            all_meanings.append(
                f"{homonym_num}. {meaning}" if len(entries) > 1 else meaning
            )
        else:
            return None  # API error

    if all_meanings and dpd_pos:
        headword_out = write_to_tsv(output_path, word, dpd_pos, " ".join(all_meanings))
        pr.yes(f"{dpd_pos}")
        open_in_goldendict(headword_out)
        return True

    pr.no("no extract")
    write_no_source(output_path, word)
    open_in_goldendict(word)
    return False


def main():
    pr.tic()
    pr.title("Extracting Cone entries")

    pth = ProjectPaths()
    output_path = Path(__file__).parent / "extract_cone.tsv"

    cone_dict = load_cone_dictionary(pth.cone_source_path)
    cone_headwords = get_cone_headwords(cone_dict)
    words_to_process, existing = prepare_word_list(
        cone_headwords, pth, output_path, source_name="cone"
    )

    state["total_words"] = len(words_to_process)
    state["remaining_words"] = words_to_process.copy()

    manager = connect_to_openrouter()

    if not output_path.exists():
        with open(output_path, "w") as f:
            f.write("headword\tdpd_pos\tmeanings\n")

    pr.green_title(f"Processing {state['total_words']} new words")
    processed = 0
    for i, word in enumerate(words_to_process, 1):
        pr.white(f"{i} / {len(words_to_process)} {word}")
        res = process_word(word, cone_dict, manager, output_path)
        if res is None:
            break  # API error
        if res:
            processed += 1
            state["processed_count"] += 1
        state["remaining_words"].remove(word)
        if i < len(words_to_process):
            time.sleep(0.5)

    pr.green_title(f"\ndone: {processed}")
    pr.info(f"total: {len(existing) + processed}")
    pr.toc()


if __name__ == "__main__":
    main()
