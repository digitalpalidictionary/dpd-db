from db.models import DpdHeadword
from gui2.needs_example import has_only_late_examples, is_missing_sutta_example


def _headword(
    source_1: str = "", source_2: str = "", meaning_1: str = ""
) -> DpdHeadword:
    hw = DpdHeadword()
    hw.source_1 = source_1
    hw.source_2 = source_2
    hw.meaning_1 = meaning_1
    return hw


class TestHasOnlyLateExamples:
    def test_late_source_1_with_no_source_2_is_late(self):
        hw = _headword(source_1="VINa 1.2.3")
        assert has_only_late_examples(hw) is True

    def test_late_source_1_and_late_source_2_is_late(self):
        hw = _headword(source_1="VINa 1.2.3", source_2="MNa 1")
        assert has_only_late_examples(hw) is True

    def test_late_source_1_with_early_source_2_is_not_late(self):
        hw = _headword(source_1="VINa 1.2.3", source_2="SN 1.1")
        assert has_only_late_examples(hw) is False

    def test_early_source_1_only_is_not_late(self):
        hw = _headword(source_1="SN 1.1")
        assert has_only_late_examples(hw) is False

    def test_early_source_1_with_late_source_2_is_not_late(self):
        # Characterizes current behavior: the function only inspects
        # source_2 lateness when source_1 is ALSO late, so an early
        # source_1 short-circuits to False regardless of source_2.
        hw = _headword(source_1="SN 1.1", source_2="VINa 1")
        assert has_only_late_examples(hw) is False

    def test_no_sources_is_not_late(self):
        hw = _headword()
        assert has_only_late_examples(hw) is False


class TestIsMissingSuttaExample:
    def test_late_examples_only_is_missing(self):
        hw = _headword(source_1="VINa 1", meaning_1="meaning here")
        assert is_missing_sutta_example(hw) is True

    def test_early_source_with_meaning_is_not_missing(self):
        hw = _headword(source_1="SN 1.1", meaning_1="meaning here")
        assert is_missing_sutta_example(hw) is False

    def test_meaning_without_source_1_is_missing(self):
        hw = _headword(meaning_1="meaning here")
        assert is_missing_sutta_example(hw) is True

    def test_no_meaning_1_is_missing(self):
        hw = _headword(source_1="SN 1.1")
        assert is_missing_sutta_example(hw) is True

    def test_nothing_set_is_missing(self):
        hw = _headword()
        assert is_missing_sutta_example(hw) is True
