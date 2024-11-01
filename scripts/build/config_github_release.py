#!/usr/bin/env python3

"""Setup config for github release."""

from rich import print

from tools.configger import config_update
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]github release config options")

    config_update("regenerate", "db_rebuild", "yes")
    config_update("regenerate", "inflections", "yes")
    config_update("regenerate", "transliterations", "yes")
    config_update("regenerate", "freq_maps", "yes")

    config_update("deconstructor", "use_premade", "yes")

    config_update("dictionary", "make_mdict", "yes")
    config_update("dictionary", "make_link", "yes")
    config_update("dictionary", "link_url", "https://thebuddhaswords.net/")
    config_update("dictionary", "extended_synonyms", "no")
    config_update("dictionary", "show_id", "no")
    config_update("dictionary", "show_ebt_count", "no")
    config_update("dictionary", "show_sbs_data", "no")
    config_update("dictionary", "show_ru_data", "no")
    config_update("dictionary", "data_limit", "0")
    
    config_update("exporter", "make_grammar", "yes")
    config_update("exporter", "make_deconstructor", "yes")
    config_update("exporter", "make_ebook", "yes")
    config_update("exporter", "tarball_db", "yes")
    config_update("exporter", "summary", "yes")

    config_update("anki", "update", "no")
    config_update("goldendict", "copy_unzip", "no")

    toc()


if __name__ == "__main__":
    main()