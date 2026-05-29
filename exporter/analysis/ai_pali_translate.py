"""Interactive Pāḷi sentence translator: analyze, AI-score, and display word-by-word grammar."""

import argparse
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

from db.db_helpers import get_db_session
from exporter.analysis.paths import ensure_analysis_dirs
from exporter.analysis.translate_core import (
    generate_markdown_report,
    translate_sentence,
)
from tools.ai_manager import AIManager
from tools.paths import ProjectPaths


def _save_markdown(report: str, sentence: str, output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    clean = re.sub(r"[^a-zA-Z]", "_", sentence[:10].lower()).strip("_")
    file_path = output_dir / f"{timestamp}_{clean}.md"
    file_path.write_text(report, encoding="utf-8")
    return file_path


def _mode_verse(book: str, verse_num: str, output_dir: Path) -> None:
    """Load an already-analysed verse from the batch JSON and render it to markdown."""
    analysis_path = ensure_analysis_dirs().output_dir / f"{book}_analysis.json"
    if not analysis_path.exists():
        print(f"Error: analysis file not found: {analysis_path}")
        sys.exit(1)

    with open(analysis_path, encoding="utf-8") as f:
        all_verses: list[dict] = json.load(f)

    verse = next((v for v in all_verses if v["num"] == verse_num), None)
    if verse is None:
        print(f"Error: verse '{verse_num}' not found in {analysis_path}")
        sys.exit(1)

    report = generate_markdown_report(verse, verse["text"])
    file_path = output_dir / f"{verse_num}.md"
    file_path.write_text(report, encoding="utf-8")
    print(f"Saved: {file_path}")
    print()
    print(report)


def _mode_interactive(output_dir: Path) -> None:
    """Interactive loop: type a Pāḷi sentence, get markdown analysis."""
    paths = ProjectPaths()
    if not paths.dpd_db_path.exists():
        print(f"Error: Database not found at {paths.dpd_db_path}")
        sys.exit(1)

    ai_manager = AIManager()

    print("--- Pāḷi AI Translator (Strict Mode) ---")
    print("Type your sentence and press Enter to translate.")
    print("Type 'x' and press Enter to exit.")
    print("-" * 26)

    while True:
        sentence = input("\nPāḷi sentence: ").strip()
        if sentence.lower() == "x":
            print("Exiting...")
            break
        if not sentence:
            continue

        db_session = get_db_session(paths.dpd_db_path)
        try:
            print(f"Analyzing: {sentence}")
            merged_result = translate_sentence(sentence, db_session, ai_manager)
            report = generate_markdown_report(merged_result, sentence)

            print("\n--- Final Analysis & Translation ---")
            print(report)
            print("---------------------------------")

            file_path = _save_markdown(report, sentence, output_dir)
            print(f"Output saved to: {file_path}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            traceback.print_exc()
        finally:
            db_session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pāḷi AI Translator — interactive or render a specific verse."
    )
    parser.add_argument("--book", help="CST book code (e.g., kn2)")
    parser.add_argument("--verse", help="Verse number to render (e.g., DHP1)")
    args = parser.parse_args()

    output_dir = ensure_analysis_dirs().output_dir

    if args.book and args.verse:
        _mode_verse(args.book, args.verse, output_dir)
    elif args.book or args.verse:
        parser.error("--book and --verse must be used together")
    else:
        _mode_interactive(output_dir)


if __name__ == "__main__":
    main()
