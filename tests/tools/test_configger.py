"""Tests for tools/configger.py defaults and build profiles.

The profile fixtures were captured from the original config_uposatha_day.py /
config_github_release.py / config_quick_profile.py scripts before their
config_update sequences were consolidated into PROFILES. Each profile must
emit the identical (section, option, value) writes in the identical order.
"""

import json
from pathlib import Path

import pytest

from tools.configger import DEFAULT_CONFIG, PROFILES

FIXTURE_PATH = Path(__file__).parent / "test_configger_fixtures.json"

PROFILE_NAMES = [
    "uposatha",
    "uposatha_reset",
    "github_release",
    "quick",
    "generate_reset",
]


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def flatten(profile: str) -> list[list[str]]:
    return [
        [section, option, value]
        for section, options in PROFILES[profile].items()
        for option, value in options.items()
    ]


def test_profile_names_match_fixture(fixtures) -> None:
    assert sorted(PROFILES) == sorted(fixtures) == sorted(PROFILE_NAMES)


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_profile_matches_original_script_writes(fixtures, profile) -> None:
    assert flatten(profile) == fixtures[profile]


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_profile_options_have_defaults(profile) -> None:
    """Every profile option needs a DEFAULT_CONFIG fallback so config_test's
    missing-key self-heal always succeeds."""
    for section, options in PROFILES[profile].items():
        for option in options:
            assert option in DEFAULT_CONFIG[section], f"{section}: {option}"


def test_make_sutta_central_default_exists() -> None:
    assert DEFAULT_CONFIG["exporter"]["make_sutta_central"] == "no"


def test_make_tbw_default_exists() -> None:
    assert DEFAULT_CONFIG["exporter"]["make_tbw"] == "no"
