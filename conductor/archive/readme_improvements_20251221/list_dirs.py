import os
from pathlib import Path
import pathspec


def list_project_dirs(root_dir="."):
    """List all directories in the project, respecting .gitignore."""
    root_path = Path(root_dir).resolve()
    gitignore_path = root_path / ".gitignore"

    patterns = []
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            patterns = f.readlines()

    # Add common defaults if not present
    if ".git/" not in patterns:
        patterns.append(".git/")
    if "__pycache__/" not in patterns:
        patterns.append("__pycache__/")

    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    project_dirs = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        rel_path = os.path.relpath(dirpath, root_path)

        # Skip the root itself from the list if desired, or handle it
        if rel_path == ".":
            # Filter dirnames in place to prevent walking into ignored dirs
            dirnames[:] = [
                d
                for d in dirnames
                if not spec.match_file(os.path.join(rel_path, d) + "/")
            ]
            continue

        # Check if the current directory is ignored
        if spec.match_file(rel_path + "/"):
            dirnames[:] = []  # Don't descend into ignored directories
            continue

        project_dirs.append(rel_path)

        # Filter dirnames to avoid walking into ignored subdirectories
        dirnames[:] = [
            d for d in dirnames if not spec.match_file(os.path.join(rel_path, d) + "/")
        ]

    return sorted(project_dirs)


if __name__ == "__main__":
    dirs = list_project_dirs()
    for d in dirs:
        print(d)
