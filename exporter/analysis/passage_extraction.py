"""Preview CST passage extraction by sutta/gāthā code without running AI analysis."""

import argparse

from exporter.analysis.paths import ensure_analysis_dirs
from exporter.analysis.passage_by_code import PassageResult, get_passage_by_code
from tools.printer import printer as pr


def format_extraction_report(result: PassageResult) -> str:
    """Format extracted passage units for terminal inspection."""
    unit = "verse" if result.is_verse else "paragraph"
    plural_unit = unit if len(result.paragraphs) == 1 else f"{unit}s"
    lines = [
        f"Source: {result.source}",
        f"Vagga/Sutta: {result.vagga}",
        f"Units: {len(result.paragraphs)} {plural_unit}",
        "",
    ]

    for index, paragraph in enumerate(result.paragraphs, 1):
        lines.extend(
            [
                f"## {unit.title()} {index}",
                paragraph,
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Preview CST passage extraction without DB or AI analysis."
    )
    parser.add_argument(
        "code",
        nargs="?",
        help="Sutta/gāthā code, e.g. AN3.12, SN12.3, DHP1, UD12, ITI37, SNP1.",
    )
    return parser.parse_args()


def main() -> None:
    """Run extraction preview from a code argument or interactive prompt."""
    ensure_analysis_dirs()
    args = parse_args()
    code = (
        args.code
        or input(
            "Enter a sutta/gāthā code (e.g. AN3.12, SN12.3, DHP1, UD12, ITI37): "
        ).strip()
    )
    if not code:
        pr.red("No code entered.")
        raise SystemExit(1)

    try:
        result = get_passage_by_code(code)
    except ValueError as exc:
        pr.red(str(exc))
        raise SystemExit(1) from exc

    pr.green(format_extraction_report(result))


if __name__ == "__main__":
    main()
