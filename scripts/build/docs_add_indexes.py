"""Auto-generate the page-link list at the bottom of each docs
submenu's index.md, driven by mkdocs.yml's nav config.
Run as part of the static.yml docs-deploy CI workflow."""

from pathlib import Path

import yaml

from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.yellow_title("adding indexes to docs")
    pth = ProjectPaths()
    docs_dir = pth.docs_dir

    with pth.mk_docs_yaml.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    nav: list = config.get("nav", [])
    for item in nav:
        if not isinstance(item, dict):
            continue

        submenu_title = next(iter(item.keys()))
        submenu_items = item[submenu_title]
        if isinstance(submenu_items, str):
            continue  # ignore items with no submenus

        pages: list[dict[str, str]] = []
        submenu_dir: str | None = None

        for entry in submenu_items:
            if isinstance(entry, str):
                # path-only entry (e.g., "features/index.md")
                path = Path(entry)
                title = path.stem  # use filename without extension
                dir_part = path.parts[0]
            elif isinstance(entry, dict):
                # title + path entry (e.g., {"Features": "features/features.md"})
                title = next(iter(entry.keys()))
                path = Path(entry[title])
                dir_part = path.parts[0]
            else:
                continue

            if path.suffix == ".md" and path.name != "index.md":
                pages.append({"title": title, "filename": path.name, "dir": dir_part})
            elif path.name == "index.md":
                submenu_dir = path.parts[0]

        if submenu_dir and pages:
            target_dir = docs_dir / submenu_dir
            index_path = target_dir / "index.md"

            with index_path.open("a", encoding="utf-8") as f:
                f.write("\n")
                for page in pages:
                    f.write(f"1. [{page['title']}]({page['filename']})\n")
            pr.green(f"generated: {index_path}")


if __name__ == "__main__":
    main()
