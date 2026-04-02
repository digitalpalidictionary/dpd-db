#!/usr/bin/env python3

"""If today is an uposatha day, update the config.ini
for creating a release."""

from tools.configger import config_update
from tools.printer import printer as pr
from tools.uposatha_day import UposathaManger


def uposatha_day_configger():
    """Updates config.ini to run all features if it's an uposatha day."""

    pr.tic()
    pr.yellow_title("uposatha day config")

    if UposathaManger.day_after_uposatha():
        config_update("exporter", "make_newsletter", "yes")
    else:
        config_update("exporter", "make_newsletter", "no")

    if UposathaManger.uposatha_today():
        pr.green_title("updating config.ini")

        config_update("regenerate", "db_rebuild", "yes")

        config_update("dictionary", "make_mdict", "yes")
        config_update("dictionary", "show_id", "no")
        config_update("dictionary", "data_limit", "0")

        config_update("deconstructor", "use_premade", "no")

        config_update("exporter", "make_grammar", "yes")
        config_update("exporter", "make_deconstructor", "yes")
        config_update("exporter", "make_ebook", "yes")
        config_update("exporter", "make_tpr", "yes")
        config_update("exporter", "make_mobile", "yes")
        config_update("exporter", "make_tbw", "yes")
        config_update("exporter", "make_pdf", "yes")
        config_update("exporter", "make_txt", "yes")
        config_update("exporter", "make_abbrev", "yes")
        config_update("exporter", "tarball_db", "yes")
        config_update("exporter", "make_changelog", "yes")
        config_update("exporter", "make_audio_db", "yes")
        config_update("exporter", "upload_audio_db", "yes")

        config_update("goldendict", "copy_unzip", "yes")
    else:
        pr.green_title("today is not an uposatha")

    pr.toc()


def uposatha_day_reset():
    """Reset exporter config to baseline after an uposatha day build."""
    pr.tic()
    pr.yellow_title("uposatha day reset")

    if not UposathaManger.uposatha_today():
        pr.green_title("today is not an uposatha")
        pr.toc()
        return

    pr.green_title("resetting config.ini")

    config_update("exporter", "make_grammar", "yes")
    config_update("exporter", "make_deconstructor", "yes")
    config_update("exporter", "make_variants", "no")
    config_update("exporter", "make_ebook", "no")
    config_update("exporter", "make_tpr", "yes")
    config_update("exporter", "make_mobile", "no")
    config_update("exporter", "make_tbw", "no")
    config_update("exporter", "make_pdf", "no")
    config_update("exporter", "make_txt", "no")
    config_update("exporter", "tarball_db", "no")
    config_update("exporter", "make_abbrev", "no")
    config_update("exporter", "make_changelog", "no")
    config_update("exporter", "update_simsapa_db", "no")
    config_update("exporter", "make_audio_db", "yes")
    config_update("exporter", "upload_audio_db", "no")

    pr.toc()


if __name__ == "__main__":
    uposatha_day_configger()
