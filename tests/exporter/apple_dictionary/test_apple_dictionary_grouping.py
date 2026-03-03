"""Tests for Apple Dictionary headword grouping functionality.

This module contains unit tests for the headword grouping logic used in
the Apple Dictionary exporter to group entries by lemma_clean.
"""

from exporter.apple_dictionary.apple_dictionary import group_headwords_by_lemma_clean


class MockHeadword:
    """Mock DpdHeadword for testing grouping logic."""

    def __init__(self, lemma_1: str):
        self._lemma_1 = lemma_1

    @property
    def lemma_1(self) -> str:
        return self._lemma_1

    @property
    def lemma_clean(self) -> str:
        import re

        return re.sub(r" \d.*$", "", self._lemma_1)

    @property
    def lemma_number(self) -> str:
        import re

        match = re.search(r" (\d+\.\d+)$", self._lemma_1)
        return match.group(1) if match else ""


class TestGroupHeadwordsByLemmaClean:
    """Test suite for group_headwords_by_lemma_clean function."""

    def test_empty_list_yields_nothing(self):
        """Test that empty input yields no groups."""
        groups = list(group_headwords_by_lemma_clean([]))
        assert groups == []

    def test_single_headword_yields_singleton_group(self):
        """Test that a single headword yields one group of size 1."""
        headwords = [MockHeadword("dhamma 1.01")]
        groups = list(group_headwords_by_lemma_clean(headwords))
        assert len(groups) == 1
        assert len(groups[0]) == 1
        assert groups[0][0].lemma_clean == "dhamma"

    def test_multiple_same_lemma_clean_grouped(self):
        """Test that multiple headwords with same lemma_clean are grouped."""
        headwords = [
            MockHeadword("dhamma 1.01"),
            MockHeadword("dhamma 1.02"),
            MockHeadword("dhamma 1.03"),
        ]
        groups = list(group_headwords_by_lemma_clean(headwords))
        assert len(groups) == 1
        assert len(groups[0]) == 3
        assert all(hw.lemma_clean == "dhamma" for hw in groups[0])

    def test_different_lemma_clean_separate_groups(self):
        """Test that different lemma_clean values yield separate groups."""
        headwords = [
            MockHeadword("dhamma 1.01"),
            MockHeadword("gacchati 1.01"),
            MockHeadword("citta 1.01"),
        ]
        groups = list(group_headwords_by_lemma_clean(headwords))
        assert len(groups) == 3
        assert groups[0][0].lemma_clean == "dhamma"
        assert groups[1][0].lemma_clean == "gacchati"
        assert groups[2][0].lemma_clean == "citta"

    def test_mixed_grouping(self):
        """Test grouping with a mix of groups and singletons."""
        headwords = [
            MockHeadword("dhamma 1.01"),
            MockHeadword("dhamma 1.02"),
            MockHeadword("gacchati 1.01"),
            MockHeadword("citta 1.01"),
            MockHeadword("citta 1.02"),
            MockHeadword("citta 1.03"),
        ]
        groups = list(group_headwords_by_lemma_clean(headwords))
        assert len(groups) == 3
        assert len(groups[0]) == 2  # dhamma group
        assert len(groups[1]) == 1  # gacchati singleton
        assert len(groups[2]) == 3  # citta group

    def test_lemma_number_extraction(self):
        """Test that lemma_number is correctly extracted from lemma_1."""
        headwords = [
            MockHeadword("dhamma 1.01"),
            MockHeadword("dhamma 2.15"),
            MockHeadword("gacchati 1.01"),
        ]
        assert headwords[0].lemma_number == "1.01"
        assert headwords[1].lemma_number == "2.15"
        assert headwords[2].lemma_number == "1.01"

    def test_headword_without_number(self):
        """Test handling of headwords without numeric suffix."""
        headwords = [MockHeadword("dhamma")]
        groups = list(group_headwords_by_lemma_clean(headwords))
        assert len(groups) == 1
        assert groups[0][0].lemma_clean == "dhamma"
        assert groups[0][0].lemma_number == ""
