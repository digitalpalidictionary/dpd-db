"""Batch-processes CST verses through AI analysis, writing results to a single JSON file."""

import argparse
import json
import sys
from typing import Any

from db.db_helpers import get_db_session
from exporter.analysis.paths import ensure_analysis_dirs
from exporter.analysis.translate_core import translate_sentence
from exporter.analysis.ui_utils import (
    _print_translation_progress,
    _write_ai_debug_artifacts,
)
from tools.ai_manager import AIManager
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    parser = argparse.ArgumentParser(
        description="Batch-process CST verses through AI analysis."
    )
    parser.add_argument("--book", required=True, help="CST book code (e.g., kn2)")
    parser.add_argument("--verse", help="Re-process a specific verse (e.g., DHP1)")
    parser.add_argument(
        "--limit", type=int, help="Limit the number of verses to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't call AI, just show what would be done",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Write raw AI responses and debug logs",
    )
    parser.add_argument(
        "--provider",
        help="Force one AI provider (requires --model), e.g. antigravity_cli",
    )
    parser.add_argument(
        "--model",
        help='Force one model (requires --provider), e.g. "Gemini 3.5 Flash (Low)"',
    )
    args = parser.parse_args()

    if bool(args.provider) != bool(args.model):
        parser.error("--provider and --model must be used together")

    book = args.book
    analysis_dirs = ensure_analysis_dirs()
    input_path = analysis_dirs.input_dir / f"{book}.json"
    output_path = analysis_dirs.output_dir / f"{book}_analysis.json"

    if not input_path.exists():
        pr.no(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        verses = json.load(f)

    # Load existing output if present for resuming
    results = []
    processed_nums = set()
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                results = json.load(f)
            # When --verse is given, drop existing entry so it gets re-processed
            if args.verse:
                results = [r for r in results if r["num"] != args.verse]
            processed_nums = {r["num"] for r in results}
            pr.green(f"Loaded {len(results)} existing results from {output_path}")
        except json.JSONDecodeError:
            pr.amber(f"Could not parse existing output {output_path}, starting fresh.")

    # Filter verses to process
    if args.verse:
        todo = [v for v in verses if v["num"] == args.verse]
        if not todo:
            pr.no(f"Verse '{args.verse}' not found in {input_path}")
            sys.exit(1)
    else:
        todo = [v for v in verses if v["num"] not in processed_nums]
        if args.limit:
            todo = todo[: args.limit]

    if not todo:
        pr.yes("No new verses to process.")
        return

    pr.green(f"Processing {len(todo)} verses...")

    paths = ProjectPaths()
    db_session = get_db_session(paths.dpd_db_path)
    ai_manager = AIManager()

    try:
        total = len(todo)
        for i, verse in enumerate(todo, 1):
            pr.green(f"[{i}/{total}] {verse['num']}")

            if args.dry_run:
                pr.yes(f"Dry-run: would process {verse['num']}")
                continue

            ai_debug: dict[str, Any] = {}
            try:
                result = translate_sentence(
                    verse["text"],
                    db_session,
                    ai_manager,
                    model=args.model,
                    provider=args.provider,
                    verse_source=verse["num"],
                    speech_mark_options=verse.get("speech_mark_options"),
                    progress=lambda event: _print_translation_progress(
                        verse["num"], event
                    ),
                    debug=ai_debug,
                    verbose=args.debug,
                )

                verse_text: str = result.get("verse_text") or verse["text"]

                entry = {
                    "num": verse["num"],
                    "vagga": verse["vagga"],
                    "text": verse["text"],
                    "verse_text": verse_text,
                    "translation": result["translation"],
                    "literal_translation": result["literal_translation"],
                    "analysis": result["analysis"],
                }

                results.append(entry)

                # Save after each verse to allow resuming
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                _write_ai_debug_artifacts(
                    verse["num"],
                    ai_debug,
                    args.debug,
                    analysis_dirs.output_dir,
                    analysis_dirs.reports_dir,
                )

            except Exception as e:  # noqa: BLE001
                pr.no(f"Error processing {verse['num']}: {e}")
                if args.debug or ai_debug:
                    ai_debug["fatal_error"] = str(e)
                    _write_ai_debug_artifacts(
                        verse["num"],
                        ai_debug,
                        args.debug,
                        analysis_dirs.output_dir,
                        analysis_dirs.reports_dir,
                    )
                # Continue with next verse instead of failing completely
                continue

        pr.yes(f"Processed {len(todo)} verses")

    finally:
        db_session.close()


if __name__ == "__main__":
    main()
