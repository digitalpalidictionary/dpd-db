#!/usr/bin/env python3

"""If today is an uposatha day, update the config.ini
for creating a release."""

from tools.configger import config_apply_profile, config_update
from tools.printer import printer as pr
from tools.uposatha_day import UposathaManger


def uposatha_day_configger() -> None:
    """Updates config.ini to run all features if it's an uposatha day."""

    pr.tic()
    pr.yellow_title("uposatha day config")

    if UposathaManger.day_after_uposatha():
        config_update("exporter", "make_newsletter", "yes")
    else:
        config_update("exporter", "make_newsletter", "no")

    if UposathaManger.uposatha_today():
        pr.green_title("updating config.ini")
        config_apply_profile("uposatha")
    else:
        pr.green_title("today is not an uposatha")

    pr.toc()


def uposatha_day_reset() -> None:
    """Reset exporter config to baseline after an uposatha day build."""
    pr.tic()
    pr.yellow_title("uposatha day reset")

    if not UposathaManger.uposatha_today():
        pr.green_title("today is not an uposatha")
        pr.toc()
        return

    pr.green_title("resetting config.ini")
    config_apply_profile("uposatha_reset")

    pr.toc()


if __name__ == "__main__":
    uposatha_day_configger()
