#!/usr/bin/env python3

"""Modules for initilizing, reading, writing, updating and testing config.ini."""

import configparser
from rich import print

config = configparser.ConfigParser()


def config_initialize():
    """Initialize config.ini."""
    config.add_section("regenerate")
    config.set("regenerate", "inflections", "yes")
    config.set("regenerate", "transliterations", "yes")
    config.set("regenerate", "freq_maps", "yes")
    config.add_section("deconstructor")
    config.set("deconstructor", "include_cloud", "no")
    config_write()


def config_read(section, option, default_value=None):
    """Read config.ini. If error, return a specified default value"""
    config.read("config.ini")
    try:
        return config.get(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default_value


def config_write():
    """Write config.ini."""
    with open("config.ini", "w") as file:
        config.write(file)


def config_update(section, option, value):
    """Update config.ini with a new section, option value."""
    config.read("config.ini")
    if config.has_section(section):
        config.set(section, option, value)
    else:
        config.add_section(section)
        config.set(section, option, value)
    config_write()


def config_test(section, option, value):
    """Test config.ini to see if a section, option equals a value."""
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
    """Test config.ini to see if a section, option exists."""
    config.read("config.ini")
    if config.has_section(section):
        return config.has_option(section, option)
    else:
        return False


if __name__ == "__main__":
    config_initialize()
