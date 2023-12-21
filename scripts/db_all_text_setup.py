#!/usr/bin/env python3

"""
Setup a config.ini "deconstructor" "all_texts" "yes" for building db for all texts
"""

from tools.configger import config_update


def main():

    config_update("deconstructor", "all_texts", "yes")
    config_update("exporter", "make_deconstructor", "yes")
    config_update("exporter", "make_grammar", "yes")
    config_update("exporter", "make_tpr", "yes")
    config_update("exporter", "make_ebook", "yes")

if __name__ == "__main__":
        main()