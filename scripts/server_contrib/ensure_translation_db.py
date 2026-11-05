"""Make sure the Tipitaka translation database is on this machine.

Run by the nightly window. `ensure_db_exists` only prints when the download
fails, so the exit code is decided here: 0 when the file exists, 1 when not."""

import sys

from tools.paths import ProjectPaths
from tools.tipitaka_db import ensure_db_exists


def main() -> int:
    paths = ProjectPaths()
    ensure_db_exists()
    if not paths.tipitaka_translation_db_path.exists():
        # A download that died part-way leaves a broken zip, and the downloader
        # skips a zip that exists, so the database would never arrive.
        paths.tipitaka_translation_db_tarball.unlink(missing_ok=True)
        ensure_db_exists()
    return 0 if paths.tipitaka_translation_db_path.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
