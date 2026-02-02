import os
from list_dirs import list_project_dirs


def check_readme_compliance(root_dir="."):
    """Check every project directory for README compliance."""
    # If we are testing on a specific root, we need to adjust list_project_dirs or its results
    # For simplicity in this script, we'll assume it's running on the project root or a test root.

    # We use a custom walk if a specific root_dir is provided that is NOT the current project root
    if root_dir != ".":
        dirs = []
        for dirpath, dirnames, filenames in os.walk(root_dir):
            rel = os.path.relpath(dirpath, root_dir)
            if rel != ".":
                dirs.append(os.path.join(root_dir, rel))
            else:
                # If root_dir itself should be checked?
                # The sub-task says "iterates through the list from list_dirs.py"
                pass
    else:
        dirs = list_project_dirs(root_dir)

    required_sections = [
        "## Purpose & Rationale",
        "## Architectural Logic",
        "## Relationships & Data Flow",
        "## Interface",
    ]

    report = {}

    for d in dirs:
        readme_path = os.path.join(d, "README.md")
        exists = os.path.exists(readme_path)
        compliant = False
        missing_sections = []

        if exists:
            with open(readme_path, "r") as f:
                content = f.read()
                missing_sections = [s for s in required_sections if s not in content]
                if not missing_sections:
                    compliant = True

        report[d] = {
            "exists": exists,
            "compliant": compliant,
            "missing_sections": missing_sections,
        }

    return report


if __name__ == "__main__":
    report = check_readme_compliance()
    missing_count = 0
    non_compliant_count = 0

    for d, info in report.items():
        if not info["exists"]:
            print(f"[MISSING] {d}/README.md")
            missing_count += 1
        elif not info["compliant"]:
            print(
                f"[NON-COMPLIANT] {d}/README.md - Missing: {', '.join(info['missing_sections'])}"
            )
            non_compliant_count += 1

    print(f"\nSummary: {missing_count} missing, {non_compliant_count} non-compliant.")
