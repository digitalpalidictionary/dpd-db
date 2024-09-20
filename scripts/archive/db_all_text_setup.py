#!/usr/bin/env python3

"""
Setup a config.ini "deconstructor" "all_texts" "yes" for building db for all texts
"""

from tools.configger import config_update, config_test


def main():

    if config_test("deconstructor", "all_texts", "no"):
        config_update("deconstructor", "all_texts", "yes")
    if config_test("exporter", "make_deconstructor", "no"):
        config_update("exporter", "make_deconstructor", "yes")
    if config_test("exporter", "make_grammar", "no"):    
        config_update("exporter", "make_grammar", "yes")
    if config_test("exporter", "make_tpr", "no"):
        config_update("exporter", "make_tpr", "yes")
    if config_test("exporter", "make_ebook", "no"):
        config_update("exporter", "make_ebook", "yes")

if __name__ == "__main__":
        main()