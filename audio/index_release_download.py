#!/usr/bin/env python3
"""Fetch the audio index TSV from the latest dpd-audio release.

Used by CI: the build pipeline only needs the small TSV (lemma_clean +
presence flags), not the 1 GB sqlite tarball.
"""

from audio.github_release import download_index, find_index_asset, get_latest_release
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.yellow_title("download audio index tsv")
    release_info = get_latest_release()
    download_index(find_index_asset(release_info))
    pr.toc()


if __name__ == "__main__":
    main()
