"""Tests for PhoneticChangeManager."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.phonetic_change_manager import PhoneticChangeManager


class TestPhoneticChangeManager:
    """Test suite for PhoneticChangeManager."""

    def test_load_tsv_success(self, tmp_path: Path) -> None:
        """Test successful TSV loading and parsing."""
        # Create test TSV
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
ati +	acc	ti > ty > cc	x	gacch	pacchājāta
"""
        tsv_file = tmp_path / "test_phonetic_changes.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        assert len(manager.rules) == 2
        assert manager.rules[0]["initial"] == "a + u"
        assert manager.rules[0]["final"] == "o"
        assert manager.rules[0]["correct"] == "au > o"
        assert manager.rules[0]["wrong"] == ["u > o"]
        assert manager.rules[0]["without"] == ["o"]
        assert manager.rules[0]["exceptions"] == ["okkhita"]

    def test_load_tsv_missing_file(self, tmp_path: Path) -> None:
        """Test handling of missing TSV file."""
        tsv_file = tmp_path / "nonexistent.tsv"

        with pytest.raises(FileNotFoundError):
            PhoneticChangeManager(str(tsv_file))

    def test_load_tsv_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty TSV file."""
        tsv_file = tmp_path / "empty.tsv"
        tsv_file.write_text("initial\tfinal\tcorrect\twrong\twithout\texceptions\n")

        manager = PhoneticChangeManager(str(tsv_file))
        assert len(manager.rules) == 0

    def test_load_tsv_with_multiple_exceptions(self, tmp_path: Path) -> None:
        """Test parsing of multiple exceptions."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
ar + t	āt	ar > ā	har > hā	x	sāttha, sātthaka 1, sātthaka 2
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))
        assert manager.rules[0]["exceptions"] == ["sāttha", "sātthaka 1", "sātthaka 2"]

    def test_process_headword_auto_add(self, tmp_path: Path) -> None:
        """Test auto_add status when phonetic is empty."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "pāpa + udaya"
        headword.construction_clean = "pāpa + udaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = ""

        result = manager.process_headword(headword)

        assert result is not None
        assert result.status == "auto_add"
        assert result.suggestion == "au > o"
        assert result.rule["initial"] == "a + u"

    def test_process_headword_auto_update(self, tmp_path: Path) -> None:
        """Test auto_update status when wrong value exists."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "pāpa + udaya"
        headword.construction_clean = "pāpa + udaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = "u > o"

        result = manager.process_headword(headword)

        assert result is not None
        assert result.status == "auto_update"
        assert result.suggestion == "au > o"

    def test_process_headword_manual_check(self, tmp_path: Path) -> None:
        """Test manual_check status when phonetic has other content."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "pāpa + udaya"
        headword.construction_clean = "pāpa + udaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = "some other change"

        result = manager.process_headword(headword)

        assert result is not None
        assert result.status == "manual_check"
        assert result.suggestion == "au > o"

    def test_process_headword_no_match(self, tmp_path: Path) -> None:
        """Test no match when criteria not met."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword that doesn't match
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "na + uppāda"
        headword.construction_clean = "na + uppāda"
        headword.root_base_clean = ""
        headword.lemma_clean = "nuppāda"
        headword.lemma_1 = "nuppāda"
        headword.phonetic = ""

        result = manager.process_headword(headword)

        assert result is None

    def test_process_headword_exception(self, tmp_path: Path) -> None:
        """Test that exceptions are respected."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword that matches but is in exceptions
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "pāpa + udaya"
        headword.construction_clean = "pāpa + udaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "okkhita"  # This is in exceptions
        headword.phonetic = ""

        result = manager.process_headword(headword)

        assert result is None

    def test_process_headword_without_exclusion(self, tmp_path: Path) -> None:
        """Test that 'without' field excludes matches."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	ū	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword that has the "without" pattern
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "pāpa + ūdaya"  # Contains ū
        headword.construction_clean = "pāpa + ūdaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = ""

        result = manager.process_headword(headword)

        assert result is None

    def test_process_headword_no_meaning(self, tmp_path: Path) -> None:
        """Test processing continues even when meaning_1 is empty."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword with no meaning
        headword = MagicMock()
        headword.meaning_1 = ""
        headword.construction = "pāpa + udaya"
        headword.construction_clean = "pāpa + udaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = ""

        result = manager.process_headword(headword)

        assert result is not None
        assert result.status == "auto_add"

    def test_process_headword_no_construction(self, tmp_path: Path) -> None:
        """Test no processing when construction is empty."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword with no construction
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = ""
        headword.construction_clean = ""
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = ""

        result = manager.process_headword(headword)

        assert result is None

    def test_process_headword_correct_already_present(self, tmp_path: Path) -> None:
        """Test no match when correct value already in phonetic."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword with correct already present
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "pāpa + udaya"
        headword.construction_clean = "pāpa + udaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = "au > o"  # Already has correct value

        result = manager.process_headword(headword)

        assert result is None

    def test_process_headword_base_match(self, tmp_path: Path) -> None:
        """Test matching against root_base_clean."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
ati	acc	ti > ty > cc	x	xyz	pacchājāta
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))

        # Create mock headword where initial matches base, not construction
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "some word"
        headword.construction_clean = "some word"
        headword.root_base_clean = "ati gacchati"  # Contains "ati"
        headword.lemma_clean = "accaya"
        headword.lemma_1 = "accaya"
        headword.phonetic = ""

        result = manager.process_headword(headword)

        assert result is not None
        assert result.status == "auto_add"

    def test_check_headword_against_rule(self, tmp_path: Path) -> None:
        """Test the optimized single-rule check method."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
ati +	acc	ti > ty > cc	x	gacch	pacchājāta
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))
        rules = manager.get_rules()

        # Create mock headword
        headword = MagicMock()
        headword.meaning_1 = "test meaning"
        headword.construction = "pāpa + udaya"
        headword.construction_clean = "pāpa + udaya"
        headword.root_base_clean = ""
        headword.lemma_clean = "pāpodaya"
        headword.lemma_1 = "pāpodaya"
        headword.phonetic = ""

        # Check first rule - should match
        result = manager.check_headword_against_rule(headword, rules[0])
        assert result is not None
        assert result.status == "auto_add"
        assert result.suggestion == "au > o"

        # Check second rule - should not match
        result = manager.check_headword_against_rule(headword, rules[1])
        assert result is None

    @patch("subprocess.Popen")
    def test_open_tsv_for_editing_libreoffice(
        self, mock_popen: MagicMock, tmp_path: Path
    ) -> None:
        """Test opening TSV with LibreOffice Calc."""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text("initial\tfinal\tcorrect\twrong\twithout\texceptions\n")

        manager = PhoneticChangeManager(str(tsv_file))
        manager.open_tsv_for_editing()

        # Should call LibreOffice Calc first
        mock_popen.assert_called_once_with(["libreoffice", "--calc", str(tsv_file)])

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_open_tsv_for_editing_fallback_linux(
        self, mock_run: MagicMock, mock_popen: MagicMock, tmp_path: Path
    ) -> None:
        """Test fallback to xdg-open when LibreOffice not found on Linux."""
        import sys

        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text("initial\tfinal\tcorrect\twrong\twithout\texceptions\n")

        manager = PhoneticChangeManager(str(tsv_file))

        # Make Popen raise FileNotFoundError to simulate missing LibreOffice
        mock_popen.side_effect = FileNotFoundError("libreoffice not found")

        with patch.object(sys, "platform", "linux"):
            manager.open_tsv_for_editing()
            # Should fallback to xdg-open
            mock_run.assert_called_once_with(["xdg-open", str(tsv_file)], check=False)

    def test_open_tsv_for_editing_missing_file(self, tmp_path: Path) -> None:
        """Test opening non-existent TSV file raises FileNotFoundError."""
        tsv_file = tmp_path / "nonexistent.tsv"
        manager = PhoneticChangeManager.__new__(PhoneticChangeManager)
        manager.tsv_path = tsv_file
        manager.rules = []

        with pytest.raises(FileNotFoundError):
            manager.open_tsv_for_editing()

    def test_get_rules_returns_list(self, tmp_path: Path) -> None:
        """Test that get_rules returns the rules list."""
        tsv_content = """initial	final	correct	wrong	without	exceptions
a + u	o	au > o	u > o	o	okkhita
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = PhoneticChangeManager(str(tsv_file))
        rules = manager.get_rules()

        assert isinstance(rules, list)
        assert len(rules) == 1
        assert rules[0]["initial"] == "a + u"
