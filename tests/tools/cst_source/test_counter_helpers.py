"""Tests for the str-only counter helpers in tools/cst_source/parsers/base.py.

The counters hold strings because heading numbers are lifted verbatim from the CST
text and are not always numeric. These tests pin the two behaviours that a later
"tidy-up" would plausibly break: bump() tolerating a non-numeric label, and
is_counted() treating "0" as unset the way the former int counters did.
"""

import pytest

from tools.cst_source.parsers.base import bump, is_counted


class TestBump:
    @pytest.mark.parametrize(
        "value,expected",
        [("0", "1"), ("1", "2"), ("9", "10"), ("421", "422")],
    )
    def test_numeric_counters_increment(self, value: str, expected: str) -> None:
        assert bump(value) == expected

    def test_step_can_exceed_one(self) -> None:
        assert bump("10", 5) == "15"

    @pytest.mark.parametrize("value", ["21-23", "(Paṭhamo bhāgo)", "", "3-4"])
    def test_non_numeric_labels_restart_from_zero(self, value: str) -> None:
        """The old int counters raised TypeError here; restarting is deliberate."""
        assert bump(value) == "1"

    def test_result_is_always_str(self) -> None:
        assert isinstance(bump("7"), str)


class TestIsCounted:
    @pytest.mark.parametrize("value", ["1", "13", "21-23", "(Paṭhamo bhāgo)"])
    def test_real_references_are_counted(self, value: str) -> None:
        assert is_counted(value) is True

    @pytest.mark.parametrize("value", ["0", ""])
    def test_zero_and_empty_are_not_counted(self, value: str) -> None:
        """Mirrors the falsiness of the former int counters: 0 and "" meant unset.

        A plain `if self.vagga_counter:` would read "0" as set and change the source
        codes of vina, kva and kn18.
        """
        assert is_counted(value) is False
