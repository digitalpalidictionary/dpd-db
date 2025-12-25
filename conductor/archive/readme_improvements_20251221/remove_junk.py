import os
from pathlib import Path

# The ones I refined and want to keep
KEEP_LIST = {
    "README.md",
    "db/README.md",
    "exporter/README.md",
    "gui/README.md",
    "tools/README.md",
    "shared_data/README.md",
    "scripts/README.md",
    "docs/README.md",
    "go_modules/README.md",
    "identity/README.md",
    "db_tests/README.md",
}

def remove_junk():
    """Removes all README.md files that were not manually refined."""
    project_root = Path(".")
    removed_count = 0
    
    for path in project_root.rglob("README.md"):
        rel_path = path.relative_to(project_root)
        
        # Skip if it's in the KEEP_LIST
        if str(rel_path) in KEEP_LIST:
            continue
            
        # Also skip if it's inside the conductor folder itself
        if "conductor" in path.parts:
            continue
            
        # Delete the junk
        path.unlink()
        removed_count += 1
        print(f"Removed junk: {rel_path}")

    print(f"\nTotal junk READMEs removed: {removed_count}")

if __name__ == "__main__":
    remove_junk()
