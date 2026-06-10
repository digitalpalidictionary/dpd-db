#!/usr/bin/env python3

"""Apply a 'quick' config.ini profile for a fast DPD-only build.

Turns off every step that can be turned off, leaving only the core DPD
GoldenDict export (no mdict) and the lookup data already in the database.

After the build the `makedict-quick` recipe calls `reset_generate_components()`,
which re-enables the [generate] gates and `make_mdict`. The remaining exporter
flags (make_grammar, make_deconstructor, make_tpr, make_audio_db, anki.update)
stay off until a full / uposatha build re-enables them, so a plain
`just makedict` straight after a quick build is still incomplete.
"""

from tools.configger import config_apply_profile
from tools.printer import printer as pr


def apply_quick_profile() -> None:
    """Set config.ini to the minimal set needed for a DPD-only build."""

    pr.tic()
    pr.yellow_title("applying makedict-quick config profile")
    config_apply_profile("quick")
    pr.toc()


def reset_generate_components() -> None:
    """Re-enable the [generate] gates so the next full makedict runs normally."""

    pr.tic()
    pr.yellow_title("re-enabling generate components")
    config_apply_profile("generate_reset")
    pr.toc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_generate_components()
    else:
        apply_quick_profile()
