#!/usr/bin/env python3

"""Setup config for uposatha day release or any other day."""

from rich import print

from tools.configger import config_update
from tools.tic_toc import tic, toc
from tools.uposatha_day import uposatha_today


def uposatha_day_configger():
    tic()
    print("[bright_yellow]uposatha day config options")
    
    if uposatha_today():
        print("[green]today is an uposatha day")

        config_update("regenerate", "db_rebuild", "yes")

        config_update("dictionary", "make_mdict", "yes")
        config_update("dictionary", "make_link", "yes")
        config_update("dictionary", "link_url", "https://thebuddhaswords.net/")
        config_update("dictionary", "extended_synonyms", "no")
        config_update("dictionary", "show_id", "no")
        config_update("dictionary", "show_ebt_count", "no")
        config_update("dictionary", "show_dps_data", "no")
        config_update("dictionary", "data_limit", "0")
        
        config_update("exporter", "make_grammar", "yes")
        config_update("exporter", "make_deconstructor", "yes")
        config_update("exporter", "make_ebook", "yes")
        config_update("exporter", "make_tpr", "yes")
        config_update("exporter", "make_tbw", "yes")
        config_update("exporter", "tarball_db", "yes")
        config_update("exporter", "summary", "yes")
    
    else:
        print("[green]today is not an uposatha day")
        config_update("exporter", "make_ebook", "no")
        config_update("exporter", "make_tpr", "yes")
        config_update("exporter", "make_tbw", "no")
        config_update("exporter", "tarball_db", "no")
        config_update("exporter", "summary", "no")
    toc()


if __name__ == "__main__":
    uposatha_day_configger()