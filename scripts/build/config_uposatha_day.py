#!/usr/bin/env python3

"""If today is an uposatha day, update the config.ini 
for creating a release."""


from tools.configger import config_update
from tools.tic_toc import tic, toc
from tools.uposatha_day import uposatha_today
from tools.printer import p_title, p_green_title, p_green, p_yes

def uposatha_day_configger():
    tic()
    p_title("uposatha day config")
    
    if uposatha_today():
        p_green("updating config.ini")

        config_update("regenerate", "db_rebuild", "yes")

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
        config_update("exporter", "make_tpr", "yes")
        config_update("exporter", "make_tbw", "yes")
        config_update("exporter", "make_pdf", "yes")
        config_update("exporter", "tarball_db", "yes")
        config_update("exporter", "summary", "yes")

        config_update("goldendict", "copy_unzip", "yes")
        p_yes("ok")
    else:
        p_green_title("today is not an uposatha")
    toc()


if __name__ == "__main__":
    uposatha_day_configger()