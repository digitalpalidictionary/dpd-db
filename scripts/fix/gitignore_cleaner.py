#!/usr/bin/env python3
"""
Check for stale .gitignore entries.
Prints lines from .gitignore that do not match any file in the project.
"""

from pathlib import Path
import pathspec
from pathspec.patterns import GitWildMatchPattern
from rich.console import Console
from rich.table import Table
import sys

def main():
    console = Console()
    
    # 1. Determine root directory (assuming script is in scripts/ or similar, or just find .gitignore)
    # We will look for .gitignore in CWD or up.
    cwd = Path.cwd()
    root = cwd
    gitignore_path = root / ".gitignore"
    
    if not gitignore_path.exists():
        # Try finding it relative to the script location if CWD is wrong?
        # But usually we run from root.
        console.print(f"[bold red]Error:[/bold red] .gitignore not found at {root}")
        sys.exit(1)

    console.print(f"[blue]Reading .gitignore from:[/blue] {gitignore_path}")

    # 2. Read .gitignore
    with open(gitignore_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 3. Collect all files and directories in the project
    # We need to walk everything, even ignored files, to see if they *would* be ignored.
    # Exclude .git directory completely.
    
    console.print("[blue]Scanning project files...[/blue]")
    all_paths = []
    
    # Using rglob or walk. walk is better to control descent into .git
    for path in root.rglob("*"):
        # Relativize
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            continue
            
        # Skip .git folder contents
        if ".git" in rel_path.parts:
            continue
            
        # pathspec expects unix style strings
        all_paths.append(rel_path.as_posix())

    console.print(f"[green]Found {len(all_paths)} files and directories.[/green]")

    # 4. Check each pattern
    unused_patterns = []

    table = Table(title="Unused .gitignore Patterns")
    table.add_column("Line", justify="right", style="cyan", no_wrap=True)
    table.add_column("Pattern", style="magenta")

    for idx, line in enumerate(lines, start=1):
        original_line = line
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue
            
        # Create a spec for just this pattern
        # GitWildMatchPattern is what git uses
        try:
            spec = pathspec.PathSpec.from_lines(GitWildMatchPattern, [line])
            
            # Check if it matches ANY file
            # match_file returns check_ignore(path) -> bool.
            # match_any returns True if any path matches.
            # wait, pathspec syntax: spec.match_file(path)
            
            # We want to know if *this pattern* matches anything.
            # For negation patterns (!foo), if 'foo' exists, does it "match"? 
            # Technically yes, the rule applies.
            
            # Optimization: match_file might be slow in loop?
            # But we have one pattern. 
            # spec.match_file(f) defaults to match_tree logic if passed a list? 
            # No, match_file takes a single path.
            
            matched = False
            for path in all_paths:
                if spec.match_file(path):
                    matched = True
                    break
            
            if not matched:
                unused_patterns.append((idx, line))
                table.add_row(str(idx), line)

        except Exception as e:
            console.print(f"[red]Error parsing line {idx}: {line} - {e}[/red]")

    if unused_patterns:
        console.print(table)
        console.print(f"\n[yellow]Found {len(unused_patterns)} unused patterns.[/yellow]")
    else:
        console.print("\n[green]All .gitignore patterns match at least one file![/green]")

if __name__ == "__main__":
    main()
