#!/usr/bin/env python3.11
# coding: utf-8

import configparser
from rich import print

config = configparser.ConfigParser()


def config_initialize():
    config.add_section("regenerate")
    config.set("regenerate", "inflections", "yes")
    config.set("regenerate", "transliterations", "yes")
    config.set("regenerate", "freq_maps", "yes")
    config_write()


def config_write():
    with open("config.ini", "w") as file:
        config.write(file)


def config_update(section, field, value):
    config.set(section, field, value)
    config_write()


def config_test(section, field, value):
    config.read("config.ini")
    if (
        section in config and 
        config.has_option(section, field)
    ):
        if config.get(section, field) == value:
            return True
        else:
            return False
    else:
        print("[red]unknown config setting")


if __name__ == "__main__":
    config_initialize()