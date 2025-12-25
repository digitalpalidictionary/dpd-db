import sys
from pathlib import Path

# Ensure we can import from the track folder
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from list_dirs import list_project_dirs
from generate_readme_draft import generate_draft

def batch_generate():
    """Finds all non-ignored directories missing README.md and generates a draft."""
    dirs = list_project_dirs()
    
    # Also check the root itself
    if not Path("README.md").exists():
        generate_draft(".")

    for d in dirs:
        readme_path = Path(d) / "README.md"
        if not readme_path.exists():
            generate_draft(d)

if __name__ == "__main__":
    batch_generate()
