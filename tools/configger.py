#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Modules for initializing, reading, writing, updating and testing
config.ini file."""

import configparser
from typing import Optional

from tools.printer import printer as pr

config = configparser.ConfigParser()
config.read("config.ini")

DEFAULT_CONFIG = {
    "version": {
        "version": "",
    },
    "regenerate": {
        "inflections": "yes",
        "transliterations": "yes",
        "freq_maps": "yes",
        "db_rebuild": "no",
    },
    "generate": {
        "suttas": "yes",
        "grammar": "yes",
        "inflections_to_headwords": "yes",
        "epd": "yes",
        "search_index": "yes",
        "deconstructor": "yes",
    },
    "gui": {
        "theme": "DarkGrey10",
        "screen_fraction_width": "0.60",
        "screen_fraction_height": "1",
        "window_x": "0",
        "window_y": "0",
        "font_name": "Noto Sans",
        "font_size": "14",
        "input_text_color": "darkgray",
        "text_color": "#00bfff",
        "element_padding_x": "0",
        "element_padding_y": "0",
        "margin_x": "0",
        "margin_y": "0",
    },
    "goldendict": {"copy_unzip": "no", "path": "", "make_slob": "no"},
    "dictionary": {
        "make_mdict": "yes",
        "show_id": "no",
        "data_limit": "0",
    },
    "exporter": {
        "make_dpd": "yes",
        "make_deconstructor": "no",
        "make_grammar": "no",
        "make_variants": "no",
        "make_tpr": "no",
        "make_mobile": "no",
        "make_ebook": "no",
        "make_tbw": "no",
        "make_sutta_central": "no",
        "make_pdf": "no",
        "make_txt": "no",
        "make_abbrev": "no",
        "tarball_db": "no",
        "make_changelog": "no",
        "make_newsletter": "no",
        "update_simsapa_db": "no",
        "make_audio_db": "yes",
        "upload_audio_db": "no",
    },
    "apis": {"openai": "", "deepseek": "", "gemini": "", "openrouter": ""},
    "anki": {"update": "no", "db_path": "", "backup_path": ""},
    "simsapa": {"app_path": "", "db_path": ""},
    "tpr": {"db_path": ""},
}

PROFILES: dict[str, dict[str, dict[str, str]]] = {
    "uposatha": {
        "regenerate": {"db_rebuild": "yes"},
        "dictionary": {"make_mdict": "yes", "show_id": "no", "data_limit": "0"},
        "generate": {
            "suttas": "yes",
            "grammar": "yes",
            "inflections_to_headwords": "yes",
            "epd": "yes",
            "search_index": "yes",
            "deconstructor": "yes",
        },
        "exporter": {
            "make_grammar": "yes",
            "make_deconstructor": "yes",
            "make_ebook": "yes",
            "make_tpr": "yes",
            "make_mobile": "yes",
            "make_tbw": "yes",
            "make_sutta_central": "yes",
            "make_pdf": "yes",
            "make_txt": "yes",
            "make_abbrev": "yes",
            "tarball_db": "yes",
            "make_changelog": "yes",
            "make_audio_db": "yes",
            "upload_audio_db": "yes",
        },
        "goldendict": {"copy_unzip": "yes"},
    },
    "uposatha_reset": {
        "exporter": {
            "make_grammar": "yes",
            "make_deconstructor": "yes",
            "make_variants": "no",
            "make_ebook": "no",
            "make_tpr": "yes",
            "make_mobile": "no",
            "make_tbw": "no",
            "make_sutta_central": "no",
            "make_pdf": "no",
            "make_txt": "no",
            "tarball_db": "no",
            "make_abbrev": "no",
            "make_changelog": "no",
            "update_simsapa_db": "no",
            "make_audio_db": "yes",
            "upload_audio_db": "no",
        },
    },
    "github_release": {
        "regenerate": {
            "db_rebuild": "yes",
            "inflections": "yes",
            "transliterations": "yes",
            "freq_maps": "yes",
        },
        "generate": {
            "deconstructor": "yes",
        },
        "dictionary": {"make_mdict": "yes", "show_id": "no", "data_limit": "0"},
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "yes",
            "make_deconstructor": "yes",
            "make_variants": "yes",
            "make_ebook": "yes",
            "make_tbw": "yes",
            "make_sutta_central": "yes",
            "tarball_db": "yes",
            "make_changelog": "yes",
            "make_tpr": "yes",
            "make_txt": "yes",
            "make_mobile": "yes",
            "make_pdf": "yes",
        },
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "no", "make_slob": "yes"},
    },
    "quick": {
        "regenerate": {
            "db_rebuild": "no",
            "inflections": "no",
            "transliterations": "no",
            "freq_maps": "no",
        },
        "generate": {
            "suttas": "no",
            "grammar": "no",
            "inflections_to_headwords": "no",
            "epd": "no",
            "search_index": "no",
            "deconstructor": "no",
        },
        "dictionary": {"make_mdict": "no"},
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "no",
            "make_deconstructor": "no",
            "make_variants": "no",
            "make_tpr": "no",
            "make_mobile": "no",
            "make_ebook": "no",
            "make_tbw": "no",
            "make_sutta_central": "no",
            "make_pdf": "no",
            "make_txt": "no",
            "make_abbrev": "no",
            "tarball_db": "no",
            "make_changelog": "no",
            "make_newsletter": "no",
            "update_simsapa_db": "no",
            "make_audio_db": "no",
            "upload_audio_db": "no",
        },
        "anki": {"update": "no"},
    },
    "generate_reset": {
        "generate": {
            "suttas": "yes",
            "grammar": "yes",
            "inflections_to_headwords": "yes",
            "epd": "yes",
            "search_index": "yes",
            "deconstructor": "yes",
        },
        "dictionary": {"make_mdict": "yes"},
    },
}


def config_initialize() -> None:
    """Initialize config.ini with default values."""
    for section, options in DEFAULT_CONFIG.items():
        if not config.has_section(section):
            config.add_section(section)
        for option, value in options.items():
            if not config.has_option(section, option):
                config.set(section, option, value)
    config_write()


def config_read(
    section: str, option: str, default_value: Optional[str] = None
) -> str | None:
    """Read config.ini. If error, return a specified default value"""
    try:
        return config.get(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default_value


def config_write() -> None:
    """Write config.ini."""
    with open("config.ini", "w", encoding="utf-8") as file:
        config.write(file)


def config_update(section: str, option: str, value, silent=False) -> None:
    """Update config.ini with a new section, option & value."""
    if config.has_section(section):
        config.set(section, option, str(value))
    else:
        config.add_section(section)
        config.set(section, option, str(value))
    config_write()
    if not silent:
        pr.green_title(f"config updated: {section}: {option} --> {value}")


def config_apply_profile(profile: str) -> None:
    """Apply a named build profile from PROFILES to config.ini."""
    for section, options in PROFILES[profile].items():
        for option, value in options.items():
            config_update(section, option, value)


def config_test(section: str, option: str, value) -> bool:
    """Test config.ini to see if a section, option equals a value."""
    if config.has_section(section) and config.has_option(section, option):
        return config.get(section, option) == str(value)
    else:
        pr.red(f"unknown config setting: {section}: {option}")
        config_update_default_value(section, option)
        return config.get(section, option, fallback="") == str(value)


def config_update_default_value(section: str, option: str) -> None:
    """Update config.ini with a default value for a missing section or option."""
    if section in DEFAULT_CONFIG and option in DEFAULT_CONFIG[section]:
        default_value = DEFAULT_CONFIG[section].get(option)
        config_update(section, option, default_value)
    else:
        pr.red(f"missing default value for {section}: {option}")


def config_test_section(section):
    """Test config.ini to see if a section exists."""
    if config.has_section(section):
        return True
    else:
        return False


def config_test_option(section, option):
    """Test config.ini to see if a section, option exists."""
    if config.has_section(section):
        return config.has_option(section, option)
    else:
        return False


def print_config_settings(sections_to_print=None) -> None:
    """Print specified sections from config.ini or all if not specified."""
    if sections_to_print is None:
        sections_to_print = config.sections()
    for section in sections_to_print:
        if config.has_section(section):
            pr.green(f"[{section}]")
            for key, value in config.items(section):
                pr.green(f"{key} = {value}")


if __name__ == "__main__":
    config_initialize()
