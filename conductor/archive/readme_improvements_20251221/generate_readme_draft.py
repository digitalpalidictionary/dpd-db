import os
import sys
from pathlib import Path

# Ensure we can import from the track folder
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def generate_draft(directory):
    """Generates a draft README.md for the given directory."""
    target_dir = Path(directory)
    if not target_dir.exists():
        print(f"Error: Directory {directory} does not exist.")
        return

    readme_path = target_dir / "README.md"
    if readme_path.exists():
        print(f"Skipping {directory}: README.md already exists.")
        return

    dir_name = target_dir.name
    
    # List files for Key Components (simple listing)
    files_list = []
    try:
        # We can't easily use the full project-wide ignore logic here without refactoring list_dirs
        # So we will do a simple list and filter typical junk
        for f in os.listdir(target_dir):
            if f.startswith(".") or f == "__pycache__":
                continue
            if (target_dir / f).is_file():
                files_list.append(f"- **{f}**")
    except Exception as e:
        print(f"Error listing files in {directory}: {e}")

    key_components = "\n".join(sorted(files_list))
    if not key_components:
        key_components = "[No files found or specific components to list]"

    template = f"""# {dir_name}/

## Purpose/Overview
[A concise summary of the directory's intent.]

## Key Components
{key_components}

## Relationships
[How the folder interacts with other parts of the system.]

## Usage/Commands
[Specific scripts or CLI commands.]
"""

    try:
        with open(readme_path, "w") as f:
            f.write(template)
        print(f"Generated draft for {directory}")
    except Exception as e:
        print(f"Failed to write README for {directory}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_readme_draft.py <directory_path>")
    else:
        generate_draft(sys.argv[1])
