"""Push the canonical CSS variables from tools/css_manager.py into the
docs site's CSS, keeping the docs styling in sync with the dictionary
CSS single source of truth. Run as part of the static.yml docs-deploy
CI workflow."""

from tools.css_manager import CSSManager


def main() -> None:
    CSSManager().update_docs_css()


if __name__ == "__main__":
    main()
