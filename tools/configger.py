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
    config.add_section("deconstructor")
    config.set("deconstructor", "include_cloud", "no")
    config_write()


def config_write():
    with open("config.ini", "w") as file:
        config.write(file)


def config_update(section, option, value):
    if config.has_section(section):
        config.set(section, option, value)
    else:
        config.add_section(section)
        config.set(section, option, value)
    config_write()


def config_test(section, option, value):
    config.read("config.ini")
    if (
        section in config and
        config.has_option(section, option)
    ):
        if config.get(section, option) == value:
            return True
        else:
            return False
    else:
        print("[red]unknown config setting")


def config_test_option(section, option):
    config.read("config.ini")
    if config.has_section(section):
        return config.has_option(section, option)
    else:
        return False


if __name__ == "__main__":
    config_initialize()
