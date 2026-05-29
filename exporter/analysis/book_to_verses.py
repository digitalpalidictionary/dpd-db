"""Extracts all verses from a CST book and writes structured JSON for batch analysis."""

import argparse
import json
import re

from exporter.analysis.paths import ensure_analysis_dirs
from gui2.dpd_fields_functions import clean_example
from tools.cst_source_sutta_example import find_cst_source_sutta_example
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager


def apply_speech_marks_to_text(
    text: str, smm: SpeechMarkManager
) -> tuple[str, dict[str, list[str]]]:
    """Apply GUI example speech-mark cleaning to passage text."""
    return clean_example(text, smm), {}


def _apply_speech_marks_verse(
    text: str, smm: SpeechMarkManager
) -> tuple[str, dict[str, list[str]]]:
    """Apply speech marks to verse text."""
    return apply_speech_marks_to_text(text, smm)


def main():
    parser = argparse.ArgumentParser(description="Extract verses from a CST book.")
    parser.add_argument(
        "--book", required=True, help="CST book code (e.g., kn2 for Dhammapada)"
    )
    args = parser.parse_args()

    book = args.book
    pr.green(f"Extracting verses from book: {book}")

    # Call find_cst_source_sutta_example with "." to match all verses/sentences
    all_examples = find_cst_source_sutta_example(book, ".")

    if not all_examples:
        pr.no(f"No verses found for book: {book}")
        return

    # Deduplicate: prefer gathas (containing \n) and avoid summaries starting with ( or [
    best_verses = {}
    for src in all_examples:
        text = src.example.strip()
        is_summary = text.startswith("(") or text.startswith("[")
        has_newline = "\n" in text

        if src.source not in best_verses:
            best_verses[src.source] = src
        else:
            current_best = best_verses[src.source]
            current_text = current_best.example.strip()
            current_is_summary = current_text.startswith(
                "("
            ) or current_text.startswith("[")
            current_has_newline = "\n" in current_text

            # Prefer non-summary
            if current_is_summary and not is_summary:
                best_verses[src.source] = src
            elif not current_is_summary and is_summary:
                pass
            # Then prefer gatha (newline)
            elif not current_has_newline and has_newline:
                best_verses[src.source] = src
            # Finally prefer shorter if both are gathas (to avoid over-capturing gatha chunks)
            # but longer if current is just a number
            elif len(text) > len(current_text) and len(current_text) < 10:
                best_verses[src.source] = src
            elif has_newline and current_has_newline and len(text) < len(current_text):
                # For gathas, sometimes the first one is the full gatha and the next one is extra
                # find_gatha_example seems to capture from the current tag backwards to the start of gatha.
                pass

    unique_verses = list(best_verses.values())

    # Sort: by numeric part of source (e.g., "DHP1" -> 1)
    def sort_key(src):
        # Extract digits from the source string
        digits = re.findall(r"\d+", src.source)
        if digits:
            # Handle cases like DHP1.1 (multi-level numbering)
            return [int(d) for d in digits]
        return [0]

    unique_verses.sort(key=sort_key)

    paths = ProjectPaths()
    smm = SpeechMarkManager(paths)

    # Build structured list with speech marks applied
    verses_data = []
    for src in unique_verses:
        processed_text, speech_mark_options = _apply_speech_marks_verse(
            src.example, smm
        )
        verse: dict = {"num": src.source, "vagga": src.sutta, "text": processed_text}
        if speech_mark_options:
            verse["speech_mark_options"] = speech_mark_options
        verses_data.append(verse)

    output_dir = ensure_analysis_dirs().input_dir
    output_path = output_dir / f"{book}.json"

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(verses_data, f, ensure_ascii=False, indent=2)

    pr.yes(f"Wrote {len(verses_data)} verses to {output_path}")


if __name__ == "__main__":
    main()
