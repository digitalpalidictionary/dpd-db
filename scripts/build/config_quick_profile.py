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

from tools.configger import config_update
from tools.printer import printer as pr


def apply_quick_profile() -> None:
    """Set config.ini to the minimal set needed for a DPD-only build."""

    pr.tic()
    pr.yellow_title("applying makedict-quick config profile")

    config_update("regenerate", "db_rebuild", "no")
    config_update("regenerate", "inflections", "no")
    config_update("regenerate", "transliterations", "no")
    config_update("regenerate", "freq_maps", "no")

    config_update("deconstructor", "use_premade", "yes")

    config_update("generate", "suttas", "no")
    config_update("generate", "grammar", "no")
    config_update("generate", "inflections_to_headwords", "no")
    config_update("generate", "epd", "no")
    config_update("generate", "search_index", "no")
    config_update("generate", "deconstructor", "no")

    config_update("dictionary", "make_mdict", "no")

    config_update("exporter", "make_dpd", "yes")
    config_update("exporter", "make_grammar", "no")
    config_update("exporter", "make_deconstructor", "no")
    config_update("exporter", "make_variants", "no")
    config_update("exporter", "make_tpr", "no")
    config_update("exporter", "make_mobile", "no")
    config_update("exporter", "make_ebook", "no")
    config_update("exporter", "make_tbw", "no")
    config_update("exporter", "make_pdf", "no")
    config_update("exporter", "make_txt", "no")
    config_update("exporter", "make_abbrev", "no")
    config_update("exporter", "tarball_db", "no")
    config_update("exporter", "make_changelog", "no")
    config_update("exporter", "make_newsletter", "no")
    config_update("exporter", "update_simsapa_db", "no")
    config_update("exporter", "make_audio_db", "no")
    config_update("exporter", "upload_audio_db", "no")

    config_update("anki", "update", "no")

    pr.toc()


def reset_generate_components() -> None:
    """Re-enable the [generate] gates so the next full makedict runs normally."""

    pr.tic()
    pr.yellow_title("re-enabling generate components")

    config_update("generate", "suttas", "yes")
    config_update("generate", "grammar", "yes")
    config_update("generate", "inflections_to_headwords", "yes")
    config_update("generate", "epd", "yes")
    config_update("generate", "search_index", "yes")
    config_update("generate", "deconstructor", "yes")

    config_update("dictionary", "make_mdict", "yes")

    pr.toc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_generate_components()
    else:
        apply_quick_profile()
