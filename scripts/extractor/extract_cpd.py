#!/usr/bin/env python3

import json
import signal
import time
from pathlib import Path

from tools.ai_open_router import OpenRouterManager
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.goldendict_tools import open_in_goldendict_os

from scripts.extractor._signal_handler import state, signal_handler
from scripts.extractor._ai_extraction import extract_with_ai
from scripts.extractor._pos_mapping import map_pos_to_dpd
from scripts.extractor._read_cpd import extract_cpd_headwords, get_cpd_html_entries
from scripts.extractor._word_list import prepare_word_list
from scripts.extractor._output import write_to_tsv, write_no_source

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

MODEL = "deepseek/deepseek-v3.2"
CPD_PROMPT = """Extract information for the Pali word {word} from this dictionary HTML.

HTML:
{html}

Look for {word} in the HTML and extract:
1. The part of speech (e.g., mfn., m., n., f., ind., etc.)
2. The English meaning/definition (semicolon-separated if multiple meanings)

Note: the word may appear with parentheses like {word_parentheses} or be abbreviated with a hyphen.

Return ONLY in this exact format:
POS | MEANING

Your response:"""

CPD_POS_MAPPING = {
    "ind": "ind",
    "ind.": "ind",
    "pron": "pron",
    "aor": "aor",
    "aor.": "aor",
    "pr": "pr",
    "pr.": "pr",
    "pr. 3 sg.": "pr",
    "pr 3 sg": "pr",
    "pr. 1 sg.": "pr",
    "pr 1 sg": "pr",
    "3. sg. pass.": "pr",
    "3.": "pr",
    "caus": "pr",
    "caus.": "pr",
    "caus. of": "pr",
    "v": "pr",
    "v.": "pr",
    "opt": "opt",
    "opt.": "opt",
    "fut": "fut",
    "fut.": "fut",
    "abs": "abs",
    "abs.": "abs",
    "pp": "pp",
    "pp.": "pp",
    "grd": "grd",
    "grd.": "grd",
}


def load_cpd_dictionary(cpd_path):
    pr.green("loading cpd dictionary")
    with open(cpd_path, "r", encoding="utf-8") as f:
        cpd_data = json.load(f)
    pr.yes(f"{len(cpd_data)}")
    return cpd_data


def process_word(word, cpd_data, manager, output_path):
    open_in_goldendict_os(word)
    entries = get_cpd_html_entries(cpd_data, word)
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
            CPD_PROMPT,
            rate_limit=5.0,
            prompt_data=prompt_data,
        )

        if result:
            cpd_pos, meaning = result
            if cpd_pos == "NOT_FOUND":
                continue
            if dpd_pos is None:
                dpd_pos = map_pos_to_dpd(cpd_pos, word, CPD_POS_MAPPING)
            all_meanings.append(
                f"{homonym_num}. {meaning}" if len(entries) > 1 else meaning
            )
        else:
            return None  # API error

    if all_meanings and dpd_pos:
        headword_out = write_to_tsv(output_path, word, dpd_pos, " ".join(all_meanings))
        pr.yes(f"{dpd_pos}")
        open_in_goldendict_os(headword_out)
        return True

    pr.no("no extract")
    write_no_source(output_path, word)
    open_in_goldendict_os(word)
    return False


def main():
    pr.tic()
    pr.title("Extracting CPD entries")

    pth = ProjectPaths()
    output_path = Path(__file__).parent / "extract_cpd.tsv"

    cpd_data = load_cpd_dictionary(pth.cpd_source_path)

    pr.green("extracting cpd headwords")
    cpd_headwords = extract_cpd_headwords(cpd_data)
    pr.yes(f"{len(cpd_headwords)}")

    words_to_process, existing = prepare_word_list(cpd_headwords, pth, output_path)
    state["total_words"] = len(words_to_process)
    state["remaining_words"] = words_to_process.copy()

    pr.green("connecting to openrouter")
    manager = OpenRouterManager()
    pr.yes("connected") if manager.client else pr.no("fail")

    if not output_path.exists():
        with open(output_path, "w") as f:
            f.write("headword\tdpd_pos\tmeanings\n")

    pr.info(f"processing {state['total_words']} new words")
    processed = 0
    for i, word in enumerate(words_to_process, 1):
        pr.white(f"{i} / {len(words_to_process)} {word}")
        res = process_word(word, cpd_data, manager, output_path)
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
