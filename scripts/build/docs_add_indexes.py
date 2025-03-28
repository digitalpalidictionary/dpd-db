import yaml
from pathlib import Path

MKDOCS_DIR = Path("mkdocs")
MKDOCS_YAML = Path("mkdocs.yaml")


def main():
    with open(MKDOCS_YAML, "r") as f:
        config = yaml.safe_load(f)

    nav = config.get("nav", [])
    for item in nav:
        if isinstance(item, dict):
            submenu_title = next(iter(item.keys()))
            submenu_items = item[submenu_title]
            # ignore items with no submenus
            if not isinstance(submenu_items, str):
                pages = []
                submenu_dir = None

                for entry in submenu_items:
                    if isinstance(entry, str):
                        # Path-only entry (e.g., "features/index.md")
                        path = Path(entry)
                        title = path.stem  # Use filename without extension
                        dir_part = path.parts[0]
                    elif isinstance(entry, dict):
                        # Title + path entry (e.g., {"Features": "features/features.md"})
                        title = next(iter(entry.keys()))
                        path = Path(entry[title])
                        dir_part = path.parts[0]

                    if path.suffix == ".md" and path.name != "index.md":
                        pages.append(
                            {"title": title, "filename": path.name, "dir": dir_part}
                        )
                    elif path.name == "index.md":
                        submenu_dir = path.parts[0]

                    if submenu_dir and pages:
                        target_dir = MKDOCS_DIR / submenu_dir
                        index_path = target_dir / "index.md"

                        with open(index_path, "a") as f:
                            for page in pages:
                                f.write(f"1. [{page['title']}]({page['filename']})\n")
                        print(f"Generated: {index_path}")


if __name__ == "__main__":
    main()
