#!/usr/bin/env python3
"""Check for stale .gitignore entries.

Reports .gitignore patterns that don't match any file currently in the
project tree. Report-only, no DB, no automatic edits — some flagged patterns
are legitimately still needed (files a build/export step generates but
hasn't run this session), so pruning is a manual, per-line judgment call."""

import sys
from pathlib import Path

import pathspec
from pathspec.patterns.gitignore import GitIgnorePatternError
from pathspec.patterns.gitwildmatch import GitWildMatchPattern
from rich.console import Console
from rich.table import Table

from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    console = Console()
    pr.yellow_title("gitignore cleaner")

    root = Path.cwd()
    gitignore_path = root / ".gitignore"

    if not gitignore_path.exists():
        console.print(f"[bold red]Error:[/bold red] .gitignore not found at {root}")
        sys.exit(1)

    console.print(f"[blue]Reading .gitignore from:[/blue] {gitignore_path}")

    with open(gitignore_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Walk everything (including normally-ignored files) so we can test
    # whether each pattern *would* match something, not just tracked files.
    console.print("[blue]Scanning project files...[/blue]")
    all_paths: list[str] = []
    for path in root.rglob("*"):
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            continue
        if ".git" in rel_path.parts:
            continue
        all_paths.append(rel_path.as_posix())

    console.print(f"[green]Found {len(all_paths)} files and directories.[/green]")

    unused_patterns: list[tuple[int, str]] = []
    table = Table(title="Unused .gitignore Patterns")
    table.add_column("Line", justify="right", style="cyan", no_wrap=True)
    table.add_column("Pattern", style="magenta")

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line or line.startswith("#") or ".DS_Store" in line:
            continue

        try:
            spec = pathspec.PathSpec.from_lines(GitWildMatchPattern, [line])
        except GitIgnorePatternError as e:
            console.print(f"[red]Error parsing line {idx}: {line} - {e}[/red]")
            continue

        matched = any(spec.match_file(p) for p in all_paths)
        if not matched:
            unused_patterns.append((idx, line))
            table.add_row(str(idx), line)

    if unused_patterns:
        console.print(table)
        console.print(
            f"\n[yellow]Found {len(unused_patterns)} unused patterns.[/yellow]"
        )
    else:
        console.print(
            "\n[green]All .gitignore patterns match at least one file![/green]"
        )

    pr.toc()


if __name__ == "__main__":
    main()
