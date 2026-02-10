"""Tests for CompoundTypeManager."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.compound_type_manager import CompoundTypeManager


class TestCompoundTypeManager:
    """Test suite for CompoundTypeManager."""

    def test_load_tsv_success(self, tmp_path: Path) -> None:
        """Test successful TSV loading and parsing."""
        # Create test TSV
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya > bahubbīhi\tx
sabba\tmasc\tfirst\tkammadhāraya\tsabbakammakkhaya
viparīta\tany\tlast\tpañcamī\tx
"""
        tsv_file = tmp_path / "test_compound_types.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        assert len(manager.rules) == 3
        assert manager.rules[0]["word"] == "sīla"
        assert manager.rules[0]["pos"] == "adj"
        assert manager.rules[0]["position"] == "last"
        assert manager.rules[0]["type"] == "kammadhāraya > bahubbīhi"
        assert manager.rules[0]["exceptions"] == ["x"]

    def test_load_tsv_missing_file(self, tmp_path: Path) -> None:
        """Test handling of missing TSV file."""
        tsv_file = tmp_path / "nonexistent.tsv"

        with pytest.raises(FileNotFoundError):
            CompoundTypeManager(str(tsv_file))

    def test_load_tsv_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty TSV file."""
        tsv_file = tmp_path / "empty.tsv"
        tsv_file.write_text("word\tpos\tposition\ttype\texceptions\n")

        manager = CompoundTypeManager(str(tsv_file))
        assert len(manager.rules) == 0

    def test_load_tsv_malformed_data(self, tmp_path: Path) -> None:
        """Test handling of malformed TSV data."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya
"""
        tsv_file = tmp_path / "malformed.tsv"
        tsv_file.write_text(tsv_content)

        # Should handle gracefully - missing exceptions field
        manager = CompoundTypeManager(str(tsv_file))
        assert len(manager.rules) == 1
        assert manager.rules[0]["exceptions"] == []

    def test_detect_compound_type_no_match(self, tmp_path: Path) -> None:
        """Test detection when no pattern matches."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        # Test with non-matching construction
        result = manager.detect_compound_type(
            construction="test construction",
            pos="adj",
            grammar=", comp",
        )
        assert result is None

    def test_detect_compound_type_match_last_position(self, tmp_path: Path) -> None:
        """Test detection with last position pattern match."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        result = manager.detect_compound_type(
            construction="saddhā sīla",
            pos="adj",
            grammar=", comp",
        )
        assert result == "kammadhāraya"

    def test_detect_compound_type_match_first_position(self, tmp_path: Path) -> None:
        """Test detection with first position pattern match."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sabba\tmasc\tfirst\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        result = manager.detect_compound_type(
            construction="sabba dhamma",
            pos="masc",
            grammar=", comp",
        )
        assert result == "kammadhāraya"

    def test_detect_compound_type_match_any_position(self, tmp_path: Path) -> None:
        """Test detection with any position pattern match."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
viparīta\tany\tlast\tpañcamī\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        result = manager.detect_compound_type(
            construction="dhamma viparīta",
            pos="adj",
            grammar=", comp",
        )
        assert result == "pañcamī"

    def test_detect_compound_type_with_exceptions(self, tmp_path: Path) -> None:
        """Test that exceptions are respected."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sabba\tmasc\tfirst\tkammadhāraya\tsabbakammakkhaya, sabbaññū
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        # Should not match for exception lemma
        result = manager.detect_compound_type(
            construction="sabba dhamma",
            pos="masc",
            grammar=", comp",
            lemma="sabbakammakkhaya",
        )
        assert result is None

    def test_detect_compound_type_pos_exclusions(self, tmp_path: Path) -> None:
        """Test that pos exclusions prevent detection."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        # Should not trigger for excluded pos
        result = manager.detect_compound_type(
            construction="saddhā sīla",
            pos="sandhi",
            grammar=", comp",
        )
        assert result is None

    def test_detect_compound_type_no_comp_grammar(self, tmp_path: Path) -> None:
        """Test that missing ', comp' in grammar prevents detection."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        result = manager.detect_compound_type(
            construction="saddhā sīla",
            pos="adj",
            grammar="nom sg",
        )
        assert result is None

    def test_detect_compound_type_empty_meaning(self, tmp_path: Path) -> None:
        """Test that empty meaning_1 prevents detection."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        result = manager.detect_compound_type(
            construction="saddhā sīla",
            pos="adj",
            grammar=", comp",
            meaning_1="",
        )
        assert result is None

    def test_detect_compound_type_existing_type(self, tmp_path: Path) -> None:
        """Test that existing compound type prevents override."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        result = manager.detect_compound_type(
            construction="saddhā sīla",
            pos="adj",
            grammar=", comp",
            compound_type="bahubbīhi",
        )
        assert result is None

    def test_detect_compound_type_multiple_types(self, tmp_path: Path) -> None:
        """Test detection with multiple possible types."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya > bahubbīhi\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))

        # When multiple types are specified, return first one
        result = manager.detect_compound_type(
            construction="saddhā sīla",
            pos="adj",
            grammar=", comp",
        )
        assert result == "kammadhāraya"

    @patch("subprocess.Popen")
    def test_open_tsv_for_editing_libreoffice(
        self, mock_popen: MagicMock, tmp_path: Path
    ) -> None:
        """Test opening TSV with LibreOffice Calc."""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text("word\tpos\tposition\ttype\texceptions\n")

        manager = CompoundTypeManager(str(tsv_file))
        manager.open_tsv_for_editing()

        # Should call LibreOffice Calc first
        mock_popen.assert_called_once_with(["libreoffice", "--calc", str(tsv_file)])

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_open_tsv_for_editing_fallback_linux(
        self, mock_run: MagicMock, mock_popen: MagicMock, tmp_path: Path
    ) -> None:
        """Test fallback to xdg-open when LibreOffice not found on Linux."""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text("word\tpos\tposition\ttype\texceptions\n")

        manager = CompoundTypeManager(str(tsv_file))

        # Make Popen raise FileNotFoundError to simulate missing LibreOffice
        mock_popen.side_effect = FileNotFoundError("libreoffice not found")

        with patch.object(sys, "platform", "linux"):
            manager.open_tsv_for_editing()
            # Should fallback to xdg-open
            mock_run.assert_called_once_with(["xdg-open", str(tsv_file)], check=False)

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_open_tsv_for_editing_fallback_darwin(
        self, mock_run: MagicMock, mock_popen: MagicMock, tmp_path: Path
    ) -> None:
        """Test fallback to open command when LibreOffice not found on macOS."""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text("word\tpos\tposition\ttype\texceptions\n")

        manager = CompoundTypeManager(str(tsv_file))

        # Make Popen raise FileNotFoundError to simulate missing LibreOffice
        mock_popen.side_effect = FileNotFoundError("libreoffice not found")

        with patch.object(sys, "platform", "darwin"):
            manager.open_tsv_for_editing()
            # Should fallback to open command
            mock_run.assert_called_once_with(["open", str(tsv_file)], check=False)

    def test_open_tsv_for_editing_missing_file(self, tmp_path: Path) -> None:
        """Test opening non-existent TSV file raises FileNotFoundError."""
        tsv_file = tmp_path / "nonexistent.tsv"
        manager = CompoundTypeManager.__new__(CompoundTypeManager)
        manager.tsv_path = tsv_file
        manager.rules = []

        with pytest.raises(FileNotFoundError):
            manager.open_tsv_for_editing()

    def test_get_rules_returns_list(self, tmp_path: Path) -> None:
        """Test that get_rules returns the rules list."""
        tsv_content = """word\tpos\tposition\ttype\texceptions
sīla\tadj\tlast\tkammadhāraya\tx
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)

        manager = CompoundTypeManager(str(tsv_file))
        rules = manager.get_rules()

        assert isinstance(rules, list)
        assert len(rules) == 1
        assert rules[0]["word"] == "sīla"
