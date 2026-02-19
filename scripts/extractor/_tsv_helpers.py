from pathlib import Path

def get_existing_headwords(output_path: Path) -> set[str]:
    """Get set of headwords already in TSV."""
    existing = set()
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            next(f, None)  # Skip header
            for line in f:
                parts = line.strip().split("\t")
                if parts:
                    existing.add(parts[0])
    return existing
