"""Interactive Stage 2: read an edited study report markdown and write a vocabulary CSV for Anki."""

import csv
from difflib import get_close_matches
import re
from pathlib import Path

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from exporter.analysis.column_options import CUSTOM, PRESETS, REGISTRY
from exporter.analysis.example_bolding import (
    bold_word_in_verse,
    find_token_in_apos_verse,
)
from exporter.analysis.paths import ensure_analysis_dirs
from exporter.analysis.passage_by_code import get_passage_by_code
from tools.paths import ProjectPaths
from tools.printer import printer as pr


_ANALYSIS_DIRS = ensure_analysis_dirs()
_REPORTS_DIR = _ANALYSIS_DIRS.reports_dir
_OUTPUT_DIR = _ANALYSIS_DIRS.output_dir


def _normalize_export_source(source: str) -> str:
    """Return the canonical source code without report or passage-selection suffixes."""
    base = source.removesuffix("_study")
    return re.sub(r"_[vp]\d+(?:-\d+)*$", "", base)


def _report_source_from_path(path: Path) -> str:
    """Return the source input that selects a report markdown file."""
    if path.stem.endswith("_study"):
        return path.stem.removesuffix("_study")
    return path.stem


def _available_report_choices(reports_dir: Path) -> list[str]:
    """Return selectable report sources from the reports directory."""
    choices: set[str] = set()
    for report_path in reports_dir.glob("*.md"):
        choices.add(_report_source_from_path(report_path))
    return sorted(choices, key=str.casefold)


def _report_choice_key(source: str) -> str:
    """Return a forgiving key for comparing user input to report sources."""
    source = source.strip().casefold().removesuffix("_study")
    return re.sub(r"[^a-z0-9.]+", "", source)


def _exact_report_choice(source: str, reports_dir: Path) -> str | None:
    """Return the available report choice matching a user source, if any."""
    source_key = _report_choice_key(source)
    for choice in _available_report_choices(reports_dir):
        if _report_choice_key(choice) == source_key:
            return choice
    return None


def _close_report_choices(source: str, reports_dir: Path, limit: int = 5) -> list[str]:
    """Return likely report choices for mistyped or partial user input."""
    source_key = _report_choice_key(source)
    choices = _available_report_choices(reports_dir)
    if not source_key:
        return []

    passage_part_pattern = re.compile(rf"^{re.escape(source_key)}[vp]\d")
    passage_part_matches = [
        choice for choice in choices if passage_part_pattern.match(_report_choice_key(choice))
    ]
    if passage_part_matches:
        return passage_part_matches[:limit]

    choice_by_key = {_report_choice_key(choice): choice for choice in choices}
    close_keys = get_close_matches(
        source_key,
        list(choice_by_key),
        n=limit,
        cutoff=0.55,
    )
    return [choice_by_key[key] for key in close_keys]


def _print_available_report_choices(reports_dir: Path) -> None:
    """Print available report files so the user can choose a valid source."""
    choices = _available_report_choices(reports_dir)
    if not choices:
        pr.amber(f"No report markdown files found in {reports_dir}")
        return

    pr.green("\nAvailable reports:")
    for source in choices:
        pr.green(f"  {source}")


def _resolve_report_path(source: str, reports_dir: Path) -> Path:
    """Return the markdown report path for a selected source."""
    source = _exact_report_choice(source, reports_dir) or source
    candidates = [
        reports_dir / f"{source}_study.md",
        reports_dir / f"{source}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _prompt_report_source(source: str, reports_dir: Path) -> str | None:
    """Prompt until the user selects an available report source or quits."""
    while True:
        if exact_choice := _exact_report_choice(source, reports_dir):
            return exact_choice

        close_choices = _close_report_choices(source, reports_dir)
        if len(close_choices) == 1:
            suggestion = close_choices[0]
            response = input(
                f"Report not found for {source!r}. Did you mean {suggestion}? "
                "[Enter/q/other]: "
            ).strip()
            if not response:
                return suggestion
            if response.casefold() == "q":
                return None
            source = response
            continue

        if close_choices:
            pr.amber(f"Report not found for {source!r}. Closest matches:")
            for counter, choice in enumerate(close_choices, start=1):
                pr.amber(f"  {counter}. {choice}")
            response = input("Type number/source, or q to quit: ").strip()
        else:
            response = input(
                f"Report not found for {source!r}. Type another source, or q to quit: "
            ).strip()

        if response.casefold() == "q":
            return None
        if response.isdigit():
            index = int(response) - 1
            if 0 <= index < len(close_choices):
                return close_choices[index]
        source = response


def _component_depth(raw_word: str) -> tuple[int, str]:
    """Return component nesting depth and clean surface word from a report cell."""
    depth = 0
    surface = raw_word.strip()
    while surface.startswith("-"):
        depth += 1
        surface = surface[1:].strip()
    return depth, surface


def _parse_report(content: str) -> tuple[str, list[tuple[int, str, str, bool]]]:
    """Extract passage plus (id, surface_word, parent_token, is_first_component) rows."""
    passage = ""
    if "### English Translation" in content:
        header_part = content.split("### English Translation")[0]
        passage_lines = [
            line for line in header_part.splitlines() if not line.startswith("#")
        ]
        passage = "\n".join(passage_lines).strip()

    rows: list[tuple[int, str, str, bool]] = []
    parent_stack: dict[int, str] = {}
    child_counts: dict[int, int] = {}
    if "### Word-by-Word Analysis" in content:
        table_part = content.split("### Word-by-Word Analysis")[1]
        for line in table_part.splitlines():
            if not line.startswith("| "):
                continue
            cells = line.split("|")
            if len(cells) < 3:
                continue
            raw_id = cells[1].strip()
            raw_word = cells[2].strip()
            if not raw_word or raw_word in {"Word in Sentence", ":---"}:
                continue
            depth, surface = _component_depth(raw_word)
            for stale_depth in list(parent_stack):
                if stale_depth > depth:
                    del parent_stack[stale_depth]
            for stale_depth in list(child_counts):
                if stale_depth > depth:
                    del child_counts[stale_depth]
            is_first_component = depth > 0 and child_counts.get(depth, 0) == 0
            parent_token = parent_stack.get(depth - 1, surface) if depth else surface
            parent_stack[depth] = surface
            child_counts[depth] = child_counts.get(depth, 0) + 1
            child_counts[depth + 1] = 0
            if raw_id.isdigit():
                rows.append((int(raw_id), surface, parent_token, is_first_component))

    return passage, rows


def _build_example(
    passage: str,
    surface: str,
    parent_token: str,
    is_first_component: bool,
    hw_id: int,
    db_session: Session,
) -> str:
    """Return the passage with a top-level row or compound component bolded."""
    is_top_level = parent_token == surface
    token = surface if is_top_level else parent_token
    apos = find_token_in_apos_verse(token, passage)
    return bold_word_in_verse(
        passage,
        apos,
        surface,
        hw_id,
        db_session,
        is_first_component=is_first_component,
        is_top_level=is_top_level,
    )


def _get_vagga(source: str) -> str:
    """Return the vagga/sutta name for a sutta code (e.g. DHP1), or '' for file sources."""
    try:
        return get_passage_by_code(_normalize_export_source(source)).vagga
    except ValueError:
        return ""


def _prompt_profile() -> list[str]:
    """Prompt the user to select basic / advanced / custom and return the column list."""
    pr.green("Column profiles:")
    pr.green(
        "  1 basic    — id, lemma_1, grammar, meaning_combo, source, sutta, example (7 cols)"
    )
    pr.green(
        f"  2 advanced — full DHP deck columns minus audio/feedback/marks/native/test/link ({len(PRESETS['advanced'])} cols)"
    )
    pr.green("  3 custom   — edit CUSTOM list in exporter/analysis/column_options.py")
    choice = input("Profile [1 basic / 2 advanced / 3 custom]: ").strip().lower()
    if choice in {"2", "advanced"}:
        return PRESETS["advanced"]
    if choice in {"3", "custom"}:
        return CUSTOM
    return PRESETS["basic"]


def main() -> None:
    paths = ProjectPaths()
    if not paths.dpd_db_path.exists():
        pr.red(f"Database not found: {paths.dpd_db_path}")
        raise SystemExit(1)

    pr.green("=" * 50)
    pr.green("Pāḷi Word Exporter — Stage 2")
    pr.green("=" * 50)

    _print_available_report_choices(_REPORTS_DIR)
    source = input(
        "\nEnter source (code or filename stem, e.g. DHP1, SN12.3_p2, my_text): "
    ).strip()
    if not source:
        pr.red("No source entered.")
        raise SystemExit(1)
    source = _prompt_report_source(source, _REPORTS_DIR)
    if source is None:
        pr.amber("Quit.")
        raise SystemExit(0)
    export_source = _normalize_export_source(source)

    report_path = _resolve_report_path(source, _REPORTS_DIR)
    if not report_path.exists():
        pr.red(f"Report not found: {report_path}")
        raise SystemExit(1)

    columns = _prompt_profile()

    content = report_path.read_text(encoding="utf-8")
    passage, id_surface_pairs = _parse_report(content)

    if not passage:
        pr.red("Could not extract passage from report.")
        raise SystemExit(1)
    if not id_surface_pairs:
        pr.red("No valid (id, word) rows found in report table.")
        raise SystemExit(1)

    pr.cyan_tmr("Retrieving vagga")
    vagga = _get_vagga(source)
    pr.yes("ok")

    db_session = get_db_session(paths.dpd_db_path)

    output_path = _OUTPUT_DIR / f"{export_source}_words.csv"
    seen_ids: set[int] = set()
    skipped = 0
    written = 0

    pr.green_tmr("Building rows")
    try:
        with output_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns, delimiter="\t")
            writer.writeheader()

            for hw_id, surface, parent_token, is_first_component in id_surface_pairs:
                if hw_id in seen_ids:
                    skipped += 1
                    continue
                seen_ids.add(hw_id)

                hw = db_session.query(DpdHeadword).filter_by(id=hw_id).first()
                if hw is None:
                    pr.amber(f"ID {hw_id} not found in DB — skipping.")
                    skipped += 1
                    continue

                example = _build_example(
                    passage=passage,
                    surface=surface,
                    parent_token=parent_token,
                    is_first_component=is_first_component,
                    hw_id=hw_id,
                    db_session=db_session,
                )

                row: dict[str, str] = {}
                for col in columns:
                    if col == "source":
                        row[col] = export_source
                    elif col == "sutta":
                        row[col] = vagga
                    elif col == "example":
                        row[col] = example
                    else:
                        extractor = REGISTRY.get(col)
                        row[col] = extractor(hw) if extractor else ""

                writer.writerow(row)
                written += 1
    finally:
        db_session.close()
    pr.yes(f"{written} rows")

    if skipped:
        pr.amber(f"{skipped} rows skipped (duplicates or missing IDs).")

    pr.green(f"\nSaved: {output_path}")
    pr.green("Import into Anki or your preferred flashcard tool.")


if __name__ == "__main__":
    main()
