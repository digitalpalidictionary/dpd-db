"""Tests for the pure functions in scripts/build/ebt_counter.py."""

import pytest

from scripts.build.ebt_counter import _merge_ebt_freq, _sya_is_ebt


# --- _sya_is_ebt ---


@pytest.mark.parametrize(
    "key,expected",
    [
        # wrong prefix
        ("other/01_foo", False),
        ("01_foo", False),
        ("", False),
        # monk vibhanga (≤2) → included
        ("canon/01_vin1", True),
        ("canon/02_vin2", True),
        # bhikkhuni vibhanga / mahavagga / cullavagga / parivara (3–8) → excluded
        ("canon/03_bar", False),
        ("canon/05_bar", False),
        ("canon/08_bar", False),
        # DN, MN, SN, AN, KN small texts (9–25) → included
        ("canon/09_dn", True),
        ("canon/15_sn", True),
        ("canon/25_kn", True),
        # vimana / jataka / niddesa / patisambhida / apadana (26–33) → excluded
        ("canon/26_vim", False),
        ("canon/33_apa", False),
        # abhidhamma (34–45) → excluded
        ("canon/34_dhs", False),
        ("canon/45_pat", False),
        # malformed: no underscore in segment → IndexError → False
        ("canon/nounderscore", False),
        # malformed: non-numeric prefix → ValueError → False
        ("canon/abc_foo", False),
    ],
)
def test_sya_is_ebt(key: str, expected: bool) -> None:
    assert _sya_is_ebt(key) is expected


# --- _merge_ebt_freq ---


def test_merge_empty_keys() -> None:
    freq: dict[str, dict[str, int]] = {"f1": {"buddho": 3}}
    assert _merge_ebt_freq(freq, []) == {}


def test_merge_missing_key_treated_as_empty() -> None:
    freq: dict[str, dict[str, int]] = {"f1": {"buddho": 3}}
    result = _merge_ebt_freq(freq, ["f2"])
    assert result == {}


def test_merge_single_key() -> None:
    freq = {"f1": {"buddho": 3, "dhammo": 5}}
    result = _merge_ebt_freq(freq, ["f1"])
    assert result == {"buddho": 3, "dhammo": 5}


def test_merge_multiple_keys_sum_overlapping_words() -> None:
    freq = {
        "f1": {"buddho": 3, "dhammo": 5},
        "f2": {"buddho": 2, "saṅgho": 4},
    }
    result = _merge_ebt_freq(freq, ["f1", "f2"])
    assert result == {"buddho": 5, "dhammo": 5, "saṅgho": 4}


def test_merge_skips_keys_not_in_freq() -> None:
    freq = {"f1": {"buddho": 1}}
    result = _merge_ebt_freq(freq, ["f1", "missing"])
    assert result == {"buddho": 1}


def test_merge_accumulates_across_three_keys() -> None:
    freq = {
        "a": {"x": 1},
        "b": {"x": 2},
        "c": {"x": 3},
    }
    result = _merge_ebt_freq(freq, ["a", "b", "c"])
    assert result == {"x": 6}
